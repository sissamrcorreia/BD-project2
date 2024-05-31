DROP TABLE IF EXISTS horario_disponivel CASCADE;

CREATE TABLE horario_disponivel (
    id SERIAL PRIMARY KEY,
    nif CHAR(9) NOT NULL REFERENCES medico,
    nome_medico VARCHAR(80),
    nome VARCHAR(80) NOT NULL REFERENCES clinica, 
    especialidade VARCHAR(80),
    hora TIME NOT NULL,
    data DATE NOT NULL,

    CONSTRAINT horario_consulta CHECK (
        (hora >= '08:00:00' AND hora < '13:00:00' AND date_part('minute', hora) IN (0, 30)) OR
        (hora >= '14:00:00' AND hora < '19:00:00' AND date_part('minute', hora) IN (0, 30))
    )
);

DO $$
DECLARE
    date_pivot DATE := '2024-01-01';
    end_date DATE := '2024-12-31';
    time_pivot TIME := '08:00:00';

    decount INT := 0;
    medico_nif CHAR(9);
    medico_nome VARCHAR(80);
    clinica VARCHAR(80);
    dia SMALLINT;
    especialidade VARCHAR(80);

    

    medico_clinica RECORD;
    
BEGIN
    
    WHILE date_pivot <= end_date LOOP
        dia := EXTRACT(ISODOW FROM date_pivot);
        
        FOR medico_clinica IN
            SELECT trabalha.NIF, trabalha.nome AS clinica_nome, medico.especialidade, medico.nome AS m_nome
            FROM trabalha JOIN medico ON medico.nif = trabalha.NIF 
            WHERE trabalha.dia_da_semana = dia
        LOOP
            time_pivot := '08:00:00';
            medico_nif := medico_clinica.nif;
            clinica :=  medico_clinica.clinica_nome;
            medico_nome := medico_clinica.m_nome;
            WHILE time_pivot < '13:00:00' LOOP
                IF NOT EXISTS (
                    SELECT 1
                    FROM consulta
                    WHERE consulta.nif = medico_nif
                    AND consulta.data = date_pivot
                    AND consulta.hora = time_pivot
                ) THEN
                    INSERT INTO horario_disponivel (nif, nome_medico,  nome, data, hora, especialidade)
                    VALUES (medico_nif, medico_nome, clinica, date_pivot, time_pivot, medico_clinica.especialidade)
                    ON CONFLICT DO NOTHING;
                END IF;
                time_pivot := time_pivot + INTERVAL '30 minutes';
            END LOOP;

            -- Parte da tarde 
            time_pivot := '14:00:00';
            WHILE time_pivot < '19:00:00' LOOP
                IF NOT EXISTS (
                    SELECT 1
                    FROM consulta
                    WHERE consulta.nif = medico_nif
                    AND consulta.data = date_pivot
                    AND consulta.hora = time_pivot
                ) THEN
                    INSERT INTO horario_disponivel (nif, nome_medico,  nome, data, hora, especialidade)
                    VALUES (medico_nif, medico_nome, clinica, date_pivot, time_pivot, medico_clinica.especialidade)
                    ON CONFLICT DO NOTHING;
                END IF;
                time_pivot := time_pivot + INTERVAL '30 minutes';
            END LOOP;

        END LOOP;
        date_pivot := date_pivot + INTERVAL '1 day';
    END LOOP;
END $$;