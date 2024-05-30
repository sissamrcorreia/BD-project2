import os
from logging.config import dictConfig
import psycopg
from flask import Flask, jsonify, request
from psycopg.rows import namedtuple_row

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
@app.route('/c/<clinica>/<especialidade>/', methods=('GET',))
def list_doctors_and_times(clinica, especialidade):
    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            medicos = cur.execute(
                """
                SELECT medico.nome, consulta.data, consulta.hora 
                FROM medico 
                JOIN consulta ON medico.nif = consulta.nif
		AND medico.especialidade = %(especialidade)s AND consulta.nome = %(clinica)s
		AND consulta.data > NOW()::date
                ORDER BY consulta.data, consulta.hora
                """,
                {"especialidade": especialidade, "clinica": clinica }
                )
            results = cur.fetchall()


    medicos = []
    for row in results:
        medicos.append({
            "NOME": row.nome,
            "ESPECIALIDADE": especialidade,

            
            
        })

    return jsonify(medicos)


# Registra uma marcação de consulta na <clinica> na base de dados (populando
# a respectiva tabela). Recebe como argumentos um paciente, um médico, e uma
# data e hora (posteriores ao momento de agendamento)
@app.route('/a/<clinica>/registar/', methods=('POST',))
def register_appointment(clinica):
    
    paciente = request.args.get("paciente")
    medico = request.args.get("medico")
    data_hora = request.args.get("data_hora")

    error = None

    if error is not None:
        return error, 400
    else:
        with psycopg.connect(conninfo=DATABASE_URL) as conn:
            with conn.cursor(row_factory=namedtuple_row) as cur:
                cur.execute(
                    #FIXME
                    """
                    INSERT INTO consulta (ssn, nif, nome, data, hora)
                    VALUES (%(paciente)s, %(medico)s, %(clinica)s, %(data_hora)s, %s) 
                    """,
                    {"clinica": clinica, "paciente": paciente, "medico": medico}, #FIXME 
                )
                conn.commit()

    return "", 204


# Cancela uma marcação de consulta que ainda não se realizou na <clinica> (o seu horário é
# posterior ao momento do cancelamento), removendo a entrada da respectiva tabela na base de
# dados. Recebe como argumentos um paciente, um médico, e uma data e hora.
@app.route('/a/<clinica>/cancelar/', methods=('DELETE',))
def cancel_appointment(clinica):
    paciente = request.args.get("paciente")
    medico = request.args.get("medico")
    data_hora = request.args.get("data_hora")

    error = None

    if error is not None:
        return error, 400
    else:
        with psycopg.connect(conninfo=DATABASE_URL) as conn:
            with conn.cursor(row_factory=namedtuple_row) as cur:
                cur.execute(
                """
                DELETE FROM consulta 
                WHERE ssn = %(paciente)s AND nif = %(medico)s AND nome = %(clinica)s 
                AND data = %s AND hora = %s
                """, 
                {"clinica": clinica, "paciente": paciente, "medico": medico}, #FIXME 
                )
                conn.commit()

    return "", 204


if __name__ == '__main__':
    app.run(debug=True)
