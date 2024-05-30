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
    dates = [current_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    current_date = start_date
    
    available_times = [f'{h:02}:{m:02}:00' for h in range(8, 13) for m in [0, 30]] + [f'{h:02}:{m:02}:00' for h in range(14, 19) for m in [0, 30]]
    
    data = {}
    consultas_by_day = {}
    for clinic in clinics:
        data.update({clinic[0]:{}})
        consultas_by_day.update({clinic[0]:{}})
        while current_date <= end_date:
            weekday = (current_date.weekday()+1)%7
            data[clinic[0]].update({current_date:{}})
            consultas_by_day[clinic[0]].update({current_date:[]})
            for t in trabalha:
                if t[1] == clinic[0] and t[2] == weekday:
                    data[clinic[0]][current_date].update({t[0]:[]})
            for medico in data[clinic[0]][current_date]:
                for hora in available_times:
                    data[clinic[0]][current_date][medico].append(hora)
            current_date += timedelta(days=1)
        current_date = start_date


    
    current_date = start_date
    while current_date <= end_date:
        consultas_by_day.update({current_date:[]})
        for clinic in clinics:
            
            # Find all medicos that work in this clinic on this day of the week
            weekday = (current_date.weekday()+1)%7
            remaining_consultations_per_clinic = 20
            #while remaining_consultations_per_clinic > 0:  # At least 20 consultations per day per clinic
                
            for medico in data[clinic[0]][current_date]:
                impossivel = False
                for i in range(2):
                    codigo_sns = f'{random.randint(100000000000, 999999999999)}'
                    while codigo_sns in used_codes:
                        codigo_sns = f'{random.randint(100000000000, 999999999999)}'
                    used_codes.append(codigo_sns)
                        
                    paciente = random.choice(pacientes)
                    while(paciente[1] == medico or paciente[0] in [c[1] for c in consultas_by_day[current_date]]):
                        paciente = random.choice(pacientes)
                        
                    consultas.append((consulta_id, paciente[0], medico, clinic[0], current_date.date().isoformat(), data[clinic[0]][current_date][medico].pop(random.randint(0,len(data[clinic[0]][current_date][medico])-1)), codigo_sns))
                    consultas_by_day[current_date].append((consulta_id, paciente[0], medico, clinic[0], current_date.date().isoformat(), data[clinic[0]][current_date][medico].pop(random.randint(0,len(data[clinic[0]][current_date][medico])-1)), codigo_sns))
                    consulta_id += 1
                    remaining_consultations_per_clinic -= 1
                    print(i, remaining_consultations_per_clinic, current_date.date().isoformat(), medico)
            while remaining_consultations_per_clinic > 0:
                medico = random.choice(list(data[clinic[0]][current_date].keys()))
                while medico == "consultas_this_day":
                    medico = random.choice(list(data[clinic[0]][current_date].keys()))
                impossivel = False
                codigo_sns = f'{random.randint(100000000000, 999999999999)}'
                while codigo_sns in used_codes:
                    codigo_sns = f'{random.randint(100000000000, 999999999999)}'
                used_codes.append(codigo_sns)
                        
                paciente = random.choice(pacientes)
                while(paciente[1] == medico or paciente[0] in [c[1] for c in consultas_by_day[current_date]]):
                    paciente = random.choice(pacientes)
                        
                hora = data[clinic[0]][current_date][medico].pop(random.randint(0,len(data[clinic[0]][current_date][medico])-1))
                consultas.append((consulta_id, paciente[0], medico, clinic[0], current_date.date().isoformat(), hora, codigo_sns))
                consultas_by_day[current_date].append((consulta_id, paciente[0], medico, clinic[0], current_date.date().isoformat(), hora, codigo_sns))
                consulta_id += 1
                remaining_consultations_per_clinic -= 1
                print(i, remaining_consultations_per_clinic, current_date.date().isoformat(), medico)
                
                
        current_date += timedelta(days=1)
        
        

        
    for paciente in pacientes:
        clinic = random.choice(clinics)
        # current_date = (start_date + (end_date - start_date) * random.random())
        # current_date = current_date.date()
        current_date = random.choice(dates)
        medico = random.choice(list(data[clinic[0]][current_date].keys()))
        while medico == "consultas_this_day":
            medico = random.choice(list(data[clinic[0]][current_date].keys()))
    
        while data[clinic[0]][current_date][medico] == [] or paciente[1] == medico or paciente[0] in [c[1] for c in consultas_by_day[current_date]]:
            #FIXME ARRANJAR MÉDICO DIFERENTE NO MESMO DIA (medicos on duty) OU JOGAR PELO SEGURO,
            #OU SEJA, ARRANJAR UM DIA DIFERENTE E SORTEAR UM MÉDICO ALOCADO NESSE DIA E CLÍNICA?
            #ATÉ SE PODE SORTEAR TUDO USANDO:
            #""
            clinic = random.choice(clinics)
            current_date = random.choice(dates)
            medico = random.choice(list(data[clinic[0]][current_date].keys()))
            while medico == "consultas_this_day":
                medico = random.choice(list(data[clinic[0]][current_date].keys()))
            #""

        consulta_id += 1
        codigo_sns = f'{random.randint(100000000000, 999999999999)}'
        while codigo_sns in used_codes:
            codigo_sns = f'{random.randint(100000000000, 999999999999)}'
        used_codes.append(codigo_sns)
        
        hora = data[clinic[0]][current_date][medico].pop(random.randint(0,len(data[clinic[0]][current_date][medico])-1))
        consultas.append((consulta_id, paciente[0], medico, clinic[0], current_date.date().isoformat(), hora, codigo_sns))
        consultas_by_day[current_date].append((consulta_id, paciente[0], medico, clinic[0], current_date.date().isoformat(), hora, codigo_sns))   
            
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
            observacoes.append((consulta[0], parametro, 'NULL'))
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
            if table == 'consulta':
                f.write(f"INSERT INTO {table} (id, ssn, nif, nome, data, hora, codigo_sns) VALUES")
                i = 0;
                for row in rows:
                    if i != 0:
                        f.write(",")
                    f.write("\n")
                    values = ', '.join(f"""'{str(value).replace("'", "''")}'""" if isinstance(value, str) else str(value) for value in row)
                    f.write(f"({values})")
                    i += 1
                f.write(";\n\n")
            elif table == 'observacao':
                f.write(f"INSERT INTO {table} (id, parametro, valor) VALUES")
                i = 0;
                for row in rows:
                    if i != 0:
                        f.write(",")
                    f.write("\n")
                    values = f"{row[0]}, '{row[1]}', {row[2]}"
                    f.write(f"({values})")
                    i += 1
                f.write(";\n\n")
            elif table == 'receita':
                f.write(f"INSERT INTO {table} (codigo_sns, medicamento, quantidade) VALUES")
                i = 0;
                for row in rows:
                    if i != 0:
                        f.write(",")
                    f.write("\n")
                    values = ', '.join(f"""'{str(value).replace("'", "''")}'""" if isinstance(value, str) else str(value) for value in row)
                    f.write(f"({values})")
                    i += 1
                f.write(";\n\n")
            else:
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
