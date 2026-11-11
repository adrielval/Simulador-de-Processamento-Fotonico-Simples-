"""
SIMULADOR FOTÔNICO SIMPLES
==========================

Objetivo:
- Simular 2 entradas ópticas (laser A e laser B).
- Cada entrada carrega 1 byte (8 bits).
- Cada bit '1' liga o laser naquele intervalo de tempo.
- Os dois sinais percorrem guias de onda com atraso e perda.
- Os sinais são combinados e detectados por um fotodetector.
- O programa estima:
    * atraso óptico em cada braço,
    * diferença de atraso,
    * potência óptica resultante bit a bit,
    * corrente do fotodetector,
    * tempo estimado por bit,
    * tempo estimado por byte.

IMPORTANTE:
Este é um modelo de estudo, não um simulador de fabricação.
Ele NÃO substitui FDTD/EME/BPM ou ferramentas como Lumerical/COMSOL/Meep.
"""

# Biblioteca matemática padrão do Python.
# Usaremos para pi, cos, raiz quadrada etc.
import math

# Biblioteca para geração opcional de gráficos.
# Mantive porque ajuda muito no estudo visual do comportamento.
import matplotlib.pyplot as plt


# Velocidade da luz no vácuo, em metros por segundo.
# Essa constante será usada para calcular o atraso de propagação.
C = 299_792_458


def db_to_linear(db_value):
    """
    Converte um valor em dB para fator linear de potência.

    Exemplo:
    - 3 dB de perda -> fator ~0.5
    - 10 dB de perda -> fator 0.1

    Parâmetro:
    - db_value: perda ou ganho em dB.

    Retorno:
    - fator linear equivalente.
    """
    return 10 ** (db_value / 10.0)


def mm_to_m(length_mm):
    """
    Converte comprimento em milímetros para metros.

    Parâmetro:
    - length_mm: comprimento em mm.

    Retorno:
    - comprimento em metros.
    """
    return length_mm / 1000.0


def nm_to_m(wavelength_nm):
    """
    Converte comprimento de onda em nanômetros para metros.

    Parâmetro:
    - wavelength_nm: comprimento de onda em nm.

    Retorno:
    - comprimento de onda em metros.
    """
    return wavelength_nm * 1e-9


def ghz_to_hz(freq_ghz):
    """
    Converte frequência em GHz para Hz.

    Parâmetro:
    - freq_ghz: frequência em gigahertz.

    Retorno:
    - frequência em hertz.
    """
    return freq_ghz * 1e9


def mw_to_w(power_mw):
    """
    Converte potência em miliwatts para watts.

    Parâmetro:
    - power_mw: potência em mW.

    Retorno:
    - potência em W.
    """
    return power_mw * 1e-3


def propagation_delay(length_mm, group_index):
    """
    Calcula o atraso de propagação no guia de onda.

    Fórmula:
    delay = L / v_g
    onde:
    v_g = c / n_g

    Logo:
    delay = L * n_g / c

    Parâmetros:
    - length_mm: comprimento do braço óptico em mm.
    - group_index: índice de grupo do guia de onda.

    Retorno:
    - atraso em segundos.
    """
    length_m = mm_to_m(length_mm)
    return (length_m * group_index) / C


def path_loss_factor(length_mm, loss_db_per_cm):
    """
    Calcula o fator linear de perda ao longo do guia.

    Entrada da perda:
    - em dB/cm, porque isso é uma forma comum de expressar perda em guias.

    Etapas:
    1. converter mm -> cm
    2. multiplicar pelo valor de perda por cm
    3. converter a perda total em dB para fator linear de potência

    Parâmetros:
    - length_mm: comprimento do braço em mm.
    - loss_db_per_cm: perda do material/guia em dB por centímetro.

    Retorno:
    - fator linear entre 0 e 1.
    """
    length_cm = length_mm / 10.0
    total_loss_db = -loss_db_per_cm * length_cm
    return db_to_linear(total_loss_db)


def phase_shift(length_mm, wavelength_nm, effective_index, initial_phase_rad):
    """
    Calcula a fase total acumulada por um braço óptico.

    Fórmula de fase:
    phi = (2*pi*n_eff*L / lambda) + fase_inicial

    Observação:
    - usamos n_eff para fase;
    - usamos n_g para atraso temporal.

    Parâmetros:
    - length_mm: comprimento do braço em mm.
    - wavelength_nm: comprimento de onda em nm.
    - effective_index: índice efetivo do modo.
    - initial_phase_rad: fase inicial do laser em radianos.

    Retorno:
    - fase total em radianos.
    """
    length_m = mm_to_m(length_mm)
    wavelength_m = nm_to_m(wavelength_nm)
    return (2.0 * math.pi * effective_index * length_m / wavelength_m) + initial_phase_rad


def rise_time_from_bandwidth(bandwidth_ghz):
    """
    Estima o tempo de subida (10% a 90%) a partir da largura de banda.

    Aproximação usada:
    tr ~= 0.35 / BW

    Essa relação é adequada para um comportamento semelhante a um
    sistema passa-baixa de 1ª ordem.

    Parâmetro:
    - bandwidth_ghz: largura de banda em GHz.

    Retorno:
    - tempo de subida em segundos.
    """
    bandwidth_hz = ghz_to_hz(bandwidth_ghz)
    return 0.35 / bandwidth_hz


def total_rise_time(source_bw_ghz, detector_bw_ghz):
    """
    Calcula o tempo de subida total do sistema.

    A ideia é combinar:
    - limitação da fonte/modulador
    - limitação do detector/eletrônica

    Combinação:
    tr_total = sqrt(tr_source^2 + tr_detector^2)

    Parâmetros:
    - source_bw_ghz: largura de banda da fonte/modulador.
    - detector_bw_ghz: largura de banda do detector.

    Retorno:
    - tupla com:
        * tr_source
        * tr_detector
        * tr_total
    """
    tr_source = rise_time_from_bandwidth(source_bw_ghz)
    tr_detector = rise_time_from_bandwidth(detector_bw_ghz)
    tr_total = math.sqrt(tr_source**2 + tr_detector**2)
    return tr_source, tr_detector, tr_total


def optical_power_after_losses(input_power_mw, length_mm, loss_db_per_cm, combiner_loss_db):
    """
    Calcula a potência óptica disponível após:
    - perda no guia
    - perda adicional no combinador/acoplador

    Parâmetros:
    - input_power_mw: potência do laser ligada, em mW.
    - length_mm: comprimento do braço.
    - loss_db_per_cm: perda no guia.
    - combiner_loss_db: perda fixa adicional no combinador.

    Retorno:
    - potência resultante em watts.
    """
    power_w = mw_to_w(input_power_mw)

    # Perda distribuída no guia.
    guide_factor = path_loss_factor(length_mm, loss_db_per_cm)

    # Perda fixa do combinador, convertida para fator linear.
    combiner_factor = db_to_linear(-combiner_loss_db)

    # Potência após ambas as perdas.
    return power_w * guide_factor * combiner_factor


def combine_powers(power_a_w, power_b_w, phase_a_rad, phase_b_rad, coherent_mode=True):
    """
    Combina as potências de dois sinais ópticos.

    Dois modos:
    1. coherent_mode = True
       Usa interferência:
       P = P1 + P2 + 2*sqrt(P1*P2)*cos(delta_phi)

    2. coherent_mode = False
       Usa soma direta de potências:
       P = P1 + P2

    Observação:
    - Se os lasers não forem coerentes entre si ou não estiverem travados em fase,
      a soma direta é mais realista para um modelo simples.

    Parâmetros:
    - power_a_w: potência do braço A em watts.
    - power_b_w: potência do braço B em watts.
    - phase_a_rad: fase do braço A.
    - phase_b_rad: fase do braço B.
    - coherent_mode: ativa ou não a interferência coerente.

    Retorno:
    - potência combinada em watts.
    """
    if coherent_mode:
        delta_phi = phase_b_rad - phase_a_rad
        combined = power_a_w + power_b_w + 2.0 * math.sqrt(power_a_w * power_b_w) * math.cos(delta_phi)

        # Por efeitos numéricos, o cálculo não deve retornar potência negativa.
        # Se houver pequeno valor negativo por arredondamento, truncamos em zero.
        return max(combined, 0.0)

    # Caso incoerente: apenas somamos as potências.
    return power_a_w + power_b_w


def photodetector_current(optical_power_w, responsivity_a_per_w):
    """
    Converte potência óptica em corrente do fotodetector.

    Fórmula:
    I = R * P

    onde:
    - I = corrente (A)
    - R = responsividade do detector (A/W)
    - P = potência óptica (W)

    Parâmetros:
    - optical_power_w: potência óptica incidente.
    - responsivity_a_per_w: responsividade do detector.

    Retorno:
    - corrente do detector em ampères.
    """
    return responsivity_a_per_w * optical_power_w


def validate_byte_string(byte_string):
    """
    Verifica se a string recebida é um byte binário válido.

    Regras:
    - deve ter exatamente 8 caracteres
    - cada caractere deve ser '0' ou '1'

    Parâmetro:
    - byte_string: texto do usuário.

    Retorno:
    - True se válido, False caso contrário.
    """
    return len(byte_string) == 8 and all(bit in "01" for bit in byte_string)


def estimate_bit_timing(delay_a_s, delay_b_s, tr_total_s):
    """
    Estima tempos importantes do sistema digital-optico.

    Ideia simples:
    - a diferença de atrasos entre os braços pode limitar a sobreposição temporal;
    - o tempo de subida total também limita a velocidade;
    - então usamos o pior caso entre ambos para um "tempo mínimo por bit" heurístico.

    Métricas:
    - delta_delay: diferença de atraso entre os braços.
    - first_bit_latency: quanto tempo o primeiro resultado leva para aparecer.
    - estimated_bit_period: período mínimo por bit (heurístico).
    - estimated_byte_time: 8 vezes o período mínimo por bit.

    Parâmetros:
    - delay_a_s: atraso do braço A.
    - delay_b_s: atraso do braço B.
    - tr_total_s: tempo de subida total do sistema.

    Retorno:
    - dicionário com os tempos estimados.
    """
    delta_delay = abs(delay_a_s - delay_b_s)

    # Latência do primeiro bit:
    # usamos o maior atraso de caminho + o tempo de subida do sistema.
    first_bit_latency = max(delay_a_s, delay_b_s) + tr_total_s

    # Estimativa simples do período mínimo por bit:
    # o sistema precisa acomodar tanto o tempo de transição quanto
    # o desalinhamento temporal entre os braços.
    estimated_bit_period = max(delta_delay, tr_total_s)

    # Tempo para 1 byte = 8 bits.
    estimated_byte_time = 8.0 * estimated_bit_period

    return {
        "delta_delay_s": delta_delay,
        "first_bit_latency_s": first_bit_latency,
        "estimated_bit_period_s": estimated_bit_period,
        "estimated_byte_time_s": estimated_byte_time,
    }


def simulate_byte_stream(
    byte_a,
    byte_b,
    input_power_a_mw,
    input_power_b_mw,
    wavelength_nm,
    length_a_mm,
    length_b_mm,
    effective_index,
    group_index,
    initial_phase_a_rad,
    initial_phase_b_rad,
    loss_db_per_cm,
    combiner_loss_db,
    detector_responsivity_a_per_w,
    source_bw_ghz,
    detector_bw_ghz,
    coherent_mode=True,
):
    """
    Função principal de simulação.

    O que ela faz:
    1. Calcula atraso e fase de cada braço.
    2. Calcula potência base disponível quando o laser está em '1'.
    3. Simula os 8 slots do byte.
    4. Para cada slot:
       - verifica se A e B estão ligados ou desligados,
       - calcula a potência combinada,
       - calcula a corrente no detector.
    5. Estima os tempos do sistema.

    Parâmetros:
    - byte_a, byte_b:
      strings de 8 bits ('01010101'), uma para cada laser.
    - input_power_a_mw, input_power_b_mw:
      potência ligada de cada laser.
    - wavelength_nm:
      comprimento de onda.
    - length_a_mm, length_b_mm:
      comprimento de cada braço óptico.
    - effective_index:
      índice efetivo para fase.
    - group_index:
      índice de grupo para atraso temporal.
    - initial_phase_a_rad, initial_phase_b_rad:
      fase inicial dos lasers.
    - loss_db_per_cm:
      perda distribuída do guia.
    - combiner_loss_db:
      perda fixa do combinador.
    - detector_responsivity_a_per_w:
      responsividade do fotodetector.
    - source_bw_ghz:
      largura de banda da fonte/modulação.
    - detector_bw_ghz:
      largura de banda do detector.
    - coherent_mode:
      ativa interferência coerente ou soma simples.

    Retorno:
    - dicionário com resultados completos da simulação.
    """
    # Validação básica dos bytes.
    if not validate_byte_string(byte_a):
        raise ValueError("byte_a deve ter exatamente 8 bits, usando apenas 0 e 1.")

    if not validate_byte_string(byte_b):
        raise ValueError("byte_b deve ter exatamente 8 bits, usando apenas 0 e 1.")

    # Atraso óptico de cada braço.
    delay_a_s = propagation_delay(length_a_mm, group_index)
    delay_b_s = propagation_delay(length_b_mm, group_index)

    # Fase total acumulada em cada braço.
    phase_a_rad = phase_shift(length_a_mm, wavelength_nm, effective_index, initial_phase_a_rad)
    phase_b_rad = phase_shift(length_b_mm, wavelength_nm, effective_index, initial_phase_b_rad)

    # Potência disponível em cada braço quando o bit está em '1'.
    on_power_a_w = optical_power_after_losses(
        input_power_mw=input_power_a_mw,
        length_mm=length_a_mm,
        loss_db_per_cm=loss_db_per_cm,
        combiner_loss_db=combiner_loss_db,
    )

    on_power_b_w = optical_power_after_losses(
        input_power_mw=input_power_b_mw,
        length_mm=length_b_mm,
        loss_db_per_cm=loss_db_per_cm,
        combiner_loss_db=combiner_loss_db,
    )

    # Tempos de subida.
    tr_source_s, tr_detector_s, tr_total_s = total_rise_time(source_bw_ghz, detector_bw_ghz)

    # Lista que guardará os resultados bit a bit.
    bit_results = []

    # Simulação dos 8 bits.
    for bit_index in range(8):
        # Lê o bit atual do laser A.
        bit_a = int(byte_a[bit_index])

        # Lê o bit atual do laser B.
        bit_b = int(byte_b[bit_index])

        # Se o bit for 1, o braço recebe potência "ligada".
        # Se o bit for 0, recebe potência zero.
        power_a_w = on_power_a_w if bit_a == 1 else 0.0
        power_b_w = on_power_b_w if bit_b == 1 else 0.0

        # Combinação das potências no ponto de leitura.
        combined_power_w = combine_powers(
            power_a_w=power_a_w,
            power_b_w=power_b_w,
            phase_a_rad=phase_a_rad,
            phase_b_rad=phase_b_rad,
            coherent_mode=coherent_mode,
        )

        # Conversão para corrente de detector.
        detector_current_a = photodetector_current(
            optical_power_w=combined_power_w,
            responsivity_a_per_w=detector_responsivity_a_per_w,
        )

        # Guarda os dados do bit atual.
        bit_results.append(
            {
                "bit_index": bit_index,
                "bit_a": bit_a,
                "bit_b": bit_b,
                "power_a_w": power_a_w,
                "power_b_w": power_b_w,
                "combined_power_w": combined_power_w,
                "detector_current_a": detector_current_a,
            }
        )

    # Estimativas temporais globais.
    timing = estimate_bit_timing(delay_a_s, delay_b_s, tr_total_s)

    # Retorno consolidado.
    return {
        "delay_a_s": delay_a_s,
        "delay_b_s": delay_b_s,
        "phase_a_rad": phase_a_rad,
        "phase_b_rad": phase_b_rad,
        "delta_phase_rad": phase_b_rad - phase_a_rad,
        "on_power_a_w": on_power_a_w,
        "on_power_b_w": on_power_b_w,
        "tr_source_s": tr_source_s,
        "tr_detector_s": tr_detector_s,
        "tr_total_s": tr_total_s,
        "timing": timing,
        "bit_results": bit_results,
    }


def print_report(results):
    """
    Exibe um relatório textual organizado da simulação.

    Parâmetro:
    - results: dicionário retornado por simulate_byte_stream().
    """
    print("\n" + "=" * 70)
    print("RELATÓRIO DA SIMULAÇÃO FOTÔNICA")
    print("=" * 70)

    print(f"Atraso braço A: {results['delay_a_s'] * 1e12:.3f} ps")
    print(f"Atraso braço B: {results['delay_b_s'] * 1e12:.3f} ps")
    print(f"Defasagem total (B - A): {results['delta_phase_rad']:.6f} rad")
    print(f"Potência ON após perdas (A): {results['on_power_a_w'] * 1e3:.6f} mW")
    print(f"Potência ON após perdas (B): {results['on_power_b_w'] * 1e3:.6f} mW")
    print(f"Tempo de subida da fonte: {results['tr_source_s'] * 1e12:.3f} ps")
    print(f"Tempo de subida do detector: {results['tr_detector_s'] * 1e12:.3f} ps")
    print(f"Tempo de subida total: {results['tr_total_s'] * 1e12:.3f} ps")

    print("\nEstimativas temporais:")
    print(f"Delta de atraso entre braços: {results['timing']['delta_delay_s'] * 1e12:.3f} ps")
    print(f"Latência do 1º bit: {results['timing']['first_bit_latency_s'] * 1e12:.3f} ps")
    print(f"Período estimado por bit: {results['timing']['estimated_bit_period_s'] * 1e12:.3f} ps")
    print(f"Tempo estimado por byte: {results['timing']['estimated_byte_time_s'] * 1e12:.3f} ps")

    print("\nTabela bit a bit:")
    print("-" * 70)
    print("idx | A | B | P_comb (mW) | I_det (mA)")
    print("-" * 70)

    for row in results["bit_results"]:
        power_mw = row["combined_power_w"] * 1e3
        current_ma = row["detector_current_a"] * 1e3
        print(f"{row['bit_index']:>3} | {row['bit_a']} | {row['bit_b']} | {power_mw:>11.6f} | {current_ma:>10.6f}")

    print("-" * 70)


def plot_results(results):
    """
    Gera gráficos simples da potência combinada e da corrente do detector.

    Isso ajuda no estudo visual do comportamento bit a bit.

    Parâmetro:
    - results: dicionário retornado por simulate_byte_stream().
    """
    # Índices dos bits no eixo X.
    x = [row["bit_index"] for row in results["bit_results"]]

    # Potência combinada em mW.
    power_mw = [row["combined_power_w"] * 1e3 for row in results["bit_results"]]

    # Corrente do detector em mA.
    current_ma = [row["detector_current_a"] * 1e3 for row in results["bit_results"]]

    plt.figure(figsize=(10, 4))
    plt.step(x, power_mw, where="mid")
    plt.xlabel("Índice do bit")
    plt.ylabel("Potência combinada (mW)")
    plt.title("Potência óptica combinada por bit")
    plt.grid(True)
    plt.show()

    plt.figure(figsize=(10, 4))
    plt.step(x, current_ma, where="mid")
    plt.xlabel("Índice do bit")
    plt.ylabel("Corrente do detector (mA)")
    plt.title("Corrente do fotodetector por bit")
    plt.grid(True)
    plt.show()


def ask_user_input():
    """
    Coleta entradas do usuário.

    Mantive tudo em uma função para:
    - deixar o código organizado,
    - facilitar futuras alterações,
    - permitir trocar depois por interface gráfica ou arquivo JSON.

    Regras:
    - Se o usuário apertar ENTER sem digitar nada,
      o programa usa um valor padrão de estudo.

    Retorno:
    - dicionário com todos os parâmetros.
    """
    print("\nDigite os parâmetros da simulação.")
    print("Se quiser usar o valor padrão sugerido, apenas pressione ENTER.\n")

    # Bytes de entrada dos dois lasers.
    byte_a = input("Byte do laser A [padrão 11001010]: ").strip() or "11001010"
    byte_b = input("Byte do laser B [padrão 10110100]: ").strip() or "10110100"

    # Potência ligada de cada laser.
    input_power_a_mw = float(input("Potência ON do laser A em mW [padrão 1.0]: ").strip() or "1.0")
    input_power_b_mw = float(input("Potência ON do laser B em mW [padrão 1.0]: ").strip() or "1.0")

    # Comprimento de onda óptico.
    wavelength_nm = float(input("Comprimento de onda em nm [padrão 1550]: ").strip() or "1550")

    # Comprimentos dos braços.
    length_a_mm = float(input("Comprimento do braço A em mm [padrão 10.0]: ").strip() or "10.0")
    length_b_mm = float(input("Comprimento do braço B em mm [padrão 10.2]: ").strip() or "10.2")

    # Índice efetivo e índice de grupo.
    effective_index = float(input("Índice efetivo n_eff [padrão 2.4]: ").strip() or "2.4")
    group_index = float(input("Índice de grupo n_g [padrão 4.2]: ").strip() or "4.2")

    # Fases iniciais.
    initial_phase_a_rad = float(input("Fase inicial do laser A em rad [padrão 0.0]: ").strip() or "0.0")
    initial_phase_b_rad = float(input("Fase inicial do laser B em rad [padrão 0.0]: ").strip() or "0.0")

    # Perdas.
    loss_db_per_cm = float(input("Perda do guia em dB/cm [padrão 1.0]: ").strip() or "1.0")
    combiner_loss_db = float(input("Perda fixa do combinador em dB [padrão 0.5]: ").strip() or "0.5")

    # Detector.
    detector_responsivity_a_per_w = float(input("Responsividade do detector em A/W [padrão 0.8]: ").strip() or "0.8")

    # Larguras de banda.
    source_bw_ghz = float(input("Largura de banda da fonte/modulador em GHz [padrão 25]: ").strip() or "25")
    detector_bw_ghz = float(input("Largura de banda do detector em GHz [padrão 20]: ").strip() or "20")

    # Modo coerente ou incoerente.
    coherent_text = input("Usar interferência coerente? (s/n) [padrão s]: ").strip().lower() or "s"
    coherent_mode = coherent_text == "s"

    return {
        "byte_a": byte_a,
        "byte_b": byte_b,
        "input_power_a_mw": input_power_a_mw,
        "input_power_b_mw": input_power_b_mw,
        "wavelength_nm": wavelength_nm,
        "length_a_mm": length_a_mm,
        "length_b_mm": length_b_mm,
        "effective_index": effective_index,
        "group_index": group_index,
        "initial_phase_a_rad": initial_phase_a_rad,
        "initial_phase_b_rad": initial_phase_b_rad,
        "loss_db_per_cm": loss_db_per_cm,
        "combiner_loss_db": combiner_loss_db,
        "detector_responsivity_a_per_w": detector_responsivity_a_per_w,
        "source_bw_ghz": source_bw_ghz,
        "detector_bw_ghz": detector_bw_ghz,
        "coherent_mode": coherent_mode,
    }


def main():
    """
    Ponto de entrada do programa.

    Fluxo:
    1. pede parâmetros ao usuário,
    2. executa simulação,
    3. imprime relatório,
    4. pergunta se o usuário deseja ver gráficos.
    """
    try:
        # Coleta os parâmetros.
        params = ask_user_input()

        # Executa a simulação usando desempacotamento do dicionário.
        results = simulate_byte_stream(**params)

        # Exibe relatório no terminal.
        print_report(results)

        # Pergunta se o usuário quer gráficos.
        show_plot = input("\nDeseja exibir os gráficos? (s/n) [padrão s]: ").strip().lower() or "s"
        if show_plot == "s":
            plot_results(results)

    except Exception as error:
        # Tratamento simples de erro para facilitar depuração.
        print(f"\nErro na execução: {error}")


# Garante que o programa só rode automaticamente
# quando este arquivo for executado diretamente.
if __name__ == "__main__":
    main()
