import random
from datetime import datetime, timedelta

nifs = set()

# Define some basic data for generating names and addresses
first_names = ['Joao', 'Maria', 'Jose', 'Ana', 'Carlos', 'Paula', 'Pedro', 'Sara', 'Miguel', 'Rita']
last_names = ['Silva', 'Santos', 'Ferreira', 'Pereira', 'Oliveira', 'Costa', 'Rodrigues', 'Martins', 'Sousa', 'Goncalves']
names = []

streets = ['Rua A', 'Rua B', 'Rua C', 'Rua D', 'Rua E']
cities = ['Lisboa', 'Sintra', 'Cascais']

# Define some specialties
specialties = ['ortopedia', 'cardiologia', 'neurologia', 'dermatologia', 'pediatria']

# Define date ranges for consultations
start_date = datetime(2023, 1, 1)
end_date = datetime(2024, 12, 31)

# Define parameters for observacoes
sintomas = [f'Sintoma {i}' for i in range(1, 51)]
metricas = [f'Metrica {i}' for i in range(1, 21)]

def random_nif():
    nif = f'{random.randint(100000000, 999999999)}'
    while nif in nifs:
        nif = f'{random.randint(100000000, 999999999)}'
    nifs.add(nif)
    return nif

def random_phone():
    return f'9{random.randint(100000000, 999999999)}'

def random_postcode():
    return f'{random.randint(1000, 9999)}-{random.randint(100, 999)}'

def random_name():
    if names == []:
        for first_name in first_names:
            for last_name in last_names:
                names.append(f'{first_name} {last_name}')
    return names.pop(random.randint(0, len(names) - 1))

def random_address():
    return f'{random.choice(streets)}, {random_postcode()} {random.choice(cities)}'

def generate_clinics():
    clinics = []
    for i in range(5):
        clinics.append((f'Clinica {chr(65 + i)}', random_phone(), random_address()))
    return clinics

def generate_enfermeiros(clinics):
    enfermeiros = []
    for clinic in clinics:
        for _ in range(6):
            enfermeiros.append((random_nif(), random_name(), random_phone(), random_address(), clinic[0]))
    return enfermeiros

def generate_medicos():
    medicos = []
    for _ in range(20):
        medicos.append((random_nif(), random_name(), random_phone(), random_address(), 'medicina geral'))
    for specialty in specialties:
        for _ in range(8):  # Adjust to distribute 60 medicos among specialties
            medicos.append((random_nif(), random_name(), random_phone(), random_address(), specialty))
    return medicos

def generate_trabalha(medicos, clinics):
    trabalha = []
    for medico in medicos:
        assigned_clinics = random.sample(clinics, 2)
        days_of_the_week = [0, 1, 2, 3, 4, 5, 6]
        for day in days_of_the_week:
            trabalha.append((medico[0], random.sample(assigned_clinics, 1)[0][0], day))
    return trabalha

def generate_pacientes(num_pacientes):
    pacientes = []
    for _ in range(num_pacientes):
        ssn = f'{random.randint(10000000000, 99999999999)}'
        while ssn in [p[0] for p in pacientes]:
            ssn = f'{random.randint(10000000000, 99999999999)}'
        pacientes.append((ssn, random_nif(), random_name(), random_phone(), random_address(), f'{random.randint(1950, 2022)}-{random.randint(1, 12):02}-{random.randint(1, 28):02}'))
    return pacientes

def generate_consultas(pacientes, medicos, clinics, trabalha, start_date, end_date):
    consultas = []
    consulta_id = 1
    used_codes = []
    used_times = []
    current_date = start_date
    while current_date <= end_date:
        for clinic in clinics:
            # Find all medicos that work in this clinic on this day of the week
            weekday = (current_date.weekday()+1)%7
            medicos_on_duty = [t[0] for t in trabalha if t[1] == clinic[0] and t[2] == weekday]
            remaining_consultations_per_clinic = 20
            while remaining_consultations_per_clinic > 0:  # At least 20 consultations per day per clinic
                available_medicos = [m for m in medicos if m[0] in medicos_on_duty]  # Ensure medico is not the same as paciente and is on duty
                if not available_medicos:
                    continue  # Skip if no available medicos for this patient at this clinic on this day
                
                
                for medico in available_medicos:
                    impossivel = False
                    used_times = set()
                    used_times = set([c[5] for c in consultas if c[4] == current_date.date().isoformat() and c[2] == medico[0]])
                    for i in range(2):
                        codigo_sns = f'{random.randint(100000000000, 999999999999)}'
                        while codigo_sns in used_codes:
                            codigo_sns = f'{random.randint(100000000000, 999999999999)}'
                            
                        hora = f'{random.choice(list(range(8, 13)) + list(range(14, 19)))}:{random.choice(["00", "30"])}:00'
                        #while hora in [c[5] for c in consultas if c[4] == current_date.date().isoformat() and c[3] == clinic[0] and c[2] == medico[0]]:
                        while hora in used_times:    
                            hora = f'{random.choice(list(range(8, 13)) + list(range(14, 19)))}:{random.choice(["00", "30"])}:00'
                            if len(used_times) == 20:
                                impossivel = True
                                break
                        if impossivel:
                            break
                        used_times.add(hora)
                        used_codes.append(codigo_sns)
                        
                        paciente = random.choice(pacientes)
                        while(paciente[1] == medico[0] or paciente[0] in [c[1] for c in consultas if c[4] == current_date.date().isoformat() and c[5] == hora]):
                            paciente = random.choice(pacientes)
                        
                        consultas.append((consulta_id, paciente[0], medico[0], clinic[0], current_date.date().isoformat(), hora, codigo_sns))
                        consulta_id += 1
                        remaining_consultations_per_clinic -= 1
                        print(i, remaining_consultations_per_clinic, current_date.date().isoformat(), medico[0])
                
        current_date += timedelta(days=1)
        
        

        
    for paciente in pacientes:
        clinic = random.choice(clinics)
        random_date = (start_date + (end_date - start_date) * random.random())
        weekday = (random_date.weekday()+1)%7
        medicos_on_duty = [t[0] for t in trabalha if t[1] == clinic[0] and t[2] == weekday]
        random_time = f'{random.choice(list(range(8, 13)) + list(range(14, 19)))}:{random.choice(["00", "30"])}:00'
        medico = random.choice(medicos_on_duty)
    
        used_times.clear()
        for i in range(len(consultas)):
            if consultas[i][2] == medico[0]:
                if consultas[i][4] == random_date.date().isoformat():
                    used_times.add(consultas[i][5])
        while random_time in used_times:
            random_time = f'{random.choice(list(range(8, 13)) + list(range(14, 19)))}:{random.choice(["00", "30"])}:00'
            if len(used_times) == 20:
                #FIXME ARRANJAR MÉDICO DIFERENTE NO MESMO DIA (medicos on duty) OU JOGAR PELO SEGURO,
                #OU SEJA, ARRANJAR UM DIA DIFERENTE E SORTEAR UM MÉDICO ALOCADO NESSE DIA E CLÍNICA?
                #ATÉ SE PODE SORTEAR TUDO USANDO:
                #""
                clinic = random.choice(clinics)
                random_date = (start_date + (end_date - start_date) * random.random())
                weekday = (random_date.weekday()+1)%7
                medicos_on_duty = [t[0] for t in trabalha if t[1] == clinic[0] and t[2] == weekday]
                medico = random.choice(medicos_on_duty)
                used_times.clear()
                for i in range(len(consultas)):
                    if consultas[i][2] == medico[0]:
                        if consultas[i][4] == random_date.date().isoformat():
                            used_times.add(consultas[i][5])
                    #""

        consulta_id += 1
        codigo_sns = f'{random.randint(100000000000, 999999999999)}'
        while codigo_sns in used_codes:
            codigo_sns = f'{random.randint(100000000000, 999999999999)}'
        consultas.append((consulta_id, paciente[0], medico, clinic[0], random_date.date().isoformat(), random_time, codigo_sns))
            
    return consultas

def generate_receitas(consultas):
    used_medication = set()
    receitas = []
    for consulta in consultas:
        used_medication.clear()
        if random.random() < 0.8:
            for _ in range(random.randint(1, 6)):
                medicamento = f'Medicamento {random.randint(1, 100)}'
                while medicamento in used_medication:
                    medicamento = f'Medicamento {random.randint(1, 100)}'
                used_medication.add(medicamento)
                quantidade = random.randint(1, 3)
                receitas.append((consulta[6], medicamento, quantidade))
    return receitas

def generate_observacoes(consultas):
    observacoes = []
    used_parameters = set()
    for consulta in consultas:
        used_parameters.clear()
        for _ in range(random.randint(1, 5)):
            parametro = random.choice(sintomas)
            while parametro in used_parameters:
                parametro = random.choice(sintomas)
            used_parameters.add(parametro)
            observacoes.append((consulta[0], parametro, "NULL"))
        for _ in range(random.randint(0, 3)):
            parametro = random.choice(metricas)
            while parametro in used_parameters:
                parametro = random.choice(metricas)
            used_parameters.add(parametro)
            valor = round(random.uniform(35.0, 40.0), 1)
            observacoes.append((consulta[0], parametro, valor))
    return observacoes

def write_to_file(filename, data):
    with open(filename, 'w') as f:
        for table, rows in data.items():
            for row in rows:
                values = ', '.join(f"""'{str(value).replace("'", "''")}'""" if isinstance(value, str) else str(value) for value in row)
                f.write(f"INSERT INTO {table} VALUES ({values});\n")

def main():
    clinics = generate_clinics()
    enfermeiros = generate_enfermeiros(clinics)
    medicos = generate_medicos()
    trabalha = generate_trabalha(medicos, clinics)
    pacientes = generate_pacientes(5000)
    consultas = generate_consultas(pacientes, medicos, clinics, trabalha, start_date, end_date)
    receitas = generate_receitas(consultas)
    observacoes = generate_observacoes(consultas)

    data = {
        'clinica': clinics,
        'enfermeiro': enfermeiros,
        'medico': medicos,
        'trabalha': trabalha,
        'paciente': pacientes,
        'consulta': consultas,
        'receita': receitas,
        'observacao': observacoes,
    }

    write_to_file('populate.sql', data)

if __name__ == "__main__":
    main()
