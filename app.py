import os
from logging.config import dictConfig
import psycopg
from flask import Flask, jsonify, request
from psycopg.rows import namedtuple_row
from datetime import datetime

app = Flask(__name__)
# DATABASE_URL environment variable if it exists, otherwise use this.
# Format postgres://username:password@hostname/database_name.

DATABASE_URL = os.environ.get("DATABASE_URL", "postgres://postgres:postgres@postgres/postgres")


# Lista todas as clínicas (nome e morada)
@app.route("/", methods=("GET",))
def clinic_index():
    """Shows all clinics: name and address"""
    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            clinicas = cur.execute(
                """
                SELECT nome, morada
                FROM clinica
                ORDER BY nome;
                """,
                {},
            ).fetchall()
    return jsonify(clinicas)


# Lista todas as especialidades oferecidas na <clinica>
@app.route("/c/<clinica>/", methods=("GET",))
def list_specialties(clinica):
    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            specialities = cur.execute(
                """
                SELECT DISTINCT especialidade 
                FROM medico 
                INNER JOIN trabalha ON medico.nif = trabalha.nif
                WHERE trabalha.nome = %(clinica)s;
                """,
                {"clinica": clinica},
            ).fetchall()
    return jsonify(specialities)


# Lista todos os médicos (nome) da <especialidade> que trabalham na <clínica> e
# primeiros três horários disponíveis p consulta d cada um deles (data e hora)
@app.route("/c/<clinica>/<especialidade>/", methods=("GET",))
def get_doctors(clinica, especialidade):
    """List all doctors with the specified specialty from the specified clinic and their first three available slots."""
    
    query_doctors = """
        SELECT DISTINCT ON (nif) nome_medico, nome, nif
        FROM horario_disponivel
        WHERE especialidade = %(especialidade)s
        AND nome = %(clinica)s

    """

    query_slots = """
        SELECT TO_CHAR(data, 'YYYY-MM-DD') as data, hora
        FROM horario_disponivel
        WHERE nif = %(nif)s AND nome = %(clinica)s
        AND (
            (data = CURRENT_DATE AND hora > CURRENT_TIME)
            OR (data > CURRENT_DATE)
        )
        ORDER BY data, hora
        LIMIT 3
    """

    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
                cur.execute("""SET TIMEZONE = 'GMT-1'""")
                cur.execute(query_doctors, {'especialidade': especialidade, 'clinica': clinica})
                doctors = cur.fetchall()

                result = []

                for doctor in doctors:
                    cur.execute(query_slots, {
                        'nif': doctor.nif,
                        'clinica': doctor.nome
                    })
                    slots = cur.fetchall()
                    
                    result.append({
                        'medico': doctor.nome_medico,
                        'vagas': [{'data': slot.data, 'hora': slot.hora.strftime('%H:%M:%S')} for slot in slots]
                    })

    return jsonify(result)



# Registra uma marcação de consulta na <clinica> na base de dados (populando
# a respectiva tabela). Recebe como argumentos um paciente, um médico, e uma
# data e hora (posteriores ao momento de agendamento)
@app.route("/a/<clinica>/registar/", methods=("POST",))
def register_appointment(clinica):
    
    paciente = request.args.get("paciente")
    medico = request.args.get("medico")
    data = request.args.get("data")
    hora = request.args.get("hora")

    if not(paciente and medico and data and hora):
        return jsonify({'ERRO': 'Preencha todos os campos.'}), 400

    try:
        data_hora = datetime.strptime(f"{data} {hora}", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return jsonify({'ERRO': 'Formato data ou hora inválido.'}), 400

    if data_hora <= datetime.now():
        return jsonify({'ERRO': 'Data e hora devem ser posteriores ao momento atual.'}), 400

    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:

            # Verifica se o médico (nif) existe.
            cur.execute(
                """
                SELECT 1
                FROM medico
                WHERE nif = %(medico)s
                """,
                {'medico': medico}
            )

            existe_medico = cur.fetchone()

            if not existe_medico:
                return jsonify({'ERRO': 'Médico não existe. Verifique se o NIF está correto.'}), 400

            # Verifica se o paciente (ssn) existe.
            cur.execute(
                """
                SELECT 1
                FROM paciente
                WHERE ssn = %(paciente)s
                """,
                {'paciente': paciente}
            )

            existe_paciente = cur.fetchone()

            if not existe_paciente:
                return jsonify({'ERRO': 'Paciente não existe. Verifique se o SSN está correto.'}), 400

            # Verifica se o medico trabalha na clinica indicada.
            cur.execute(
                """
                SELECT 1
                FROM trabalha
                WHERE nif = %(medico)s
                AND nome = %(clinica)s
                """,
                {"medico": medico, "clinica": clinica},
            )
            medico_trabalha_clinica = cur.fetchone()

            if not medico_trabalha_clinica:
                return jsonify({'ERRO': 'Médico com o NIF indicado não trabalha nesta clinica.'}), 400

            
            # Verifica se há disponibilidade
            cur.execute(
                """
                SELECT 1
                FROM horario_disponivel
                WHERE nif = %(medico)s
                AND nome = %(clinica)s
                AND data = %(data)s
                AND hora = %(hora)s
                """,
                {"clinica": clinica, "data": data, "hora": hora, "medico": medico},
            )
            disponibilidade = cur.fetchone(),

            if not disponibilidade[0]:
                return jsonify({'ERRO': 'Médico não tem disponibilidade para a data e hora especificadas.'}), 400
            else: 
        
                cur.execute(
                    """
                    DELETE FROM horario_disponivel
                    WHERE nif = %(medico)s
                    AND nome = %(clinica)s
                    AND data = %(data)s
                    AND hora = %(hora)s
                    """,
                    {"clinica": clinica, "data": data, "hora": hora, "medico": medico}
                )

                cur.execute(
                    """
                    SELECT MAX(id) FROM consulta
                    """
                )

                next_id = cur.fetchone()[0] + 1


                cur.execute(
                    """
                    INSERT INTO consulta (id, ssn, nif, nome, data, hora) VALUES
                    (%(id)s, %(paciente)s, %(medico)s, %(clinica)s, %(data)s, %(hora)s)
                    """,
                    {"id": next_id, "clinica": clinica, "data": data, "hora": hora, "medico": medico, "paciente": paciente},
                )

                return "Marcação concluida com sucesso!", 200

            


# Cancela uma marcação de consulta que ainda não se realizou na <clinica> (o seu horário é
# posterior ao momento do cancelamento), removendo a entrada da respectiva tabela na base de
# dados. Recebe como argumentos um paciente, um médico, e uma data e hora.
@app.route('/a/<clinica>/cancelar/', methods=('POST',))
def cancel_appointment(clinica):
    
    paciente = request.args.get("paciente")
    medico = request.args.get("medico")
    data = request.args.get("data")
    hora = request.args.get("hora")

    if not(paciente and medico and data and hora):
        return jsonify({'ERRO': 'Preencha todos os campos.'}), 400

    try:
        data_hora = datetime.strptime(f"{data} {hora}", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return jsonify({'ERRO': 'Formato data ou hora inválido.'}), 400

    if data_hora <= datetime.now():
        return jsonify({'ERRO': 'Data e hora devem ser posteriores ao momento atual.'}), 400

    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            conn.autocommit = False

            # Verifica se o médico (nif) existe.
            cur.execute(
                """
                SELECT 1
                FROM medico
                WHERE nif = %(medico)s
                """,
                {'medico': medico}
            )

            existe_medico = cur.fetchone()

            if not existe_medico:
                return jsonify({'ERRO': 'Médico não existe. Verifique se o NIF está correto.'}), 400

            # Verifica se o paciente (ssn) existe.
            cur.execute(
                """
                SELECT 1
                FROM paciente
                WHERE ssn = %(paciente)s
                """,
                {'paciente': paciente}
            )

            existe_paciente = cur.fetchone()

            if not existe_paciente:
                return jsonify({'ERRO': 'Paciente não existe. Verifique se o SSN está correto.'}), 400


            # Verifica se o medico trabalha na clinica indicada.
            cur.execute(
                """
                SELECT 1
                FROM trabalha
                WHERE nif = %(medico)s
                AND nome = %(clinica)s
                """,
                {"medico": medico, "clinica": clinica},
            )
            medico_trabalha_clinica = cur.fetchone()

            if not medico_trabalha_clinica:
                return jsonify({'ERRO': 'Médico com o NIF indicado não trabalha nesta clinica.'}), 400

            
            # Verifica se há consulta
            cur.execute(
                """
                SELECT 1
                FROM consulta
                WHERE nif = %(medico)s
                AND nome = %(clinica)s
                AND data = %(data)s
                AND hora = %(hora)s
                """,
                {"clinica": clinica, "data": data, "hora": hora, "medico": medico},
            )
            marcacao = cur.fetchone(),

            if not marcacao[0]:
                return jsonify({'ERRO': 'Médico não tem consulta agendada para a data e hora especificadas.'}), 400
            else: 

                # Apagar id da observação 
                cur.execute(
                    """
                    DELETE FROM observacao USING consulta
                    WHERE observacao.id = consulta.id
                    AND consulta.nif = %(medico)s
                    AND consulta.nome = %(clinica)s
                    AND consulta.data = %(data)s
                    AND consulta.hora = %(hora)s
                    """,
                    {"clinica": clinica, "data": data, "hora": hora, "medico": medico}
                )

                # Apagar codigo_sns da receita
                cur.execute(
                    """
                    DELETE FROM receita USING consulta
                    WHERE receita.codigo_sns = consulta.codigo_sns
                    AND consulta.nif = %(medico)s
                    AND consulta.nome = %(clinica)s
                    AND consulta.data = %(data)s
                    AND consulta.hora = %(hora)s
                    """,
                    {"clinica": clinica, "data": data, "hora": hora, "medico": medico}
                )
        
                # Apagar da tabela consulta
                cur.execute(
                    """
                    DELETE FROM consulta
                    WHERE nif = %(medico)s
                    AND nome = %(clinica)s
                    AND data = %(data)s
                    AND hora = %(hora)s
                    """,
                    {"clinica": clinica, "data": data, "hora": hora, "medico": medico}
                )

                # Obter especialidade
                cur.execute(
                    """
                    SELECT especialidade FROM medico
                    WHERE nif = %(medico)s
                    """,
                    {"medico": medico}
                )
                especildade = cur.fetchone()[0]

                # Obter o nome do medico
                cur.execute(
                    """
                    SELECT nome FROM medico
                    WHERE nif = %(medico)s
                    """,
                    {"medico": medico}
                )
                nome_medico = cur.fetchone()[0]

                # Obter o ultimo id do horario_disponivel
                cur.execute(
                    """
                    SELECT MAX(id) FROM horario_disponivel
                    """
                )
                next_id = cur.fetchone()[0] + 1
                
                # Adicionar nova disponibilidade
                cur.execute(
                    """
                    INSERT INTO horario_disponivel (id, nif, nome, data, hora, nome_medico, especialidade) VALUES
                    (%(id)s, %(medico)s, %(clinica)s, %(data)s, %(hora)s, %(nome_medico)s, %(especialidade)s)
                    """,
                    {"id": next_id, "clinica": clinica, "data": data, "hora": hora, "medico": medico,
                     "nome_medico": nome_medico, "especialidade": especildade},
                )
                conn.commit()
                return "Marcação removida com sucesso!", 200


if __name__ == '__main__':
    app.run(debug=True)

