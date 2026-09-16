from machine import Pin, ADC, I2C
from time import sleep, ticks_ms, ticks_diff
from pico_i2c_lcd import I2cLcd

# config do i2c
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)

# config do lcd
lcd = I2cLcd(i2c, 0x27, 2, 16)

# config dos leds
led_vermelho = Pin(4, Pin.OUT)
led_amarelo = Pin(3, Pin.OUT)
led_verde = Pin(2, Pin.OUT)

# config botao
botao_decimal = Pin(7, Pin.IN, Pin.PULL_UP)
botao_binario = Pin(8, Pin.IN, Pin.PULL_UP)
botao_hexdecmal = Pin(9, Pin.IN, Pin.PULL_UP)


# texto, linha, delay, limpar tela anterior
def print_to_lcd(str, line, delay, should_clear_screen):

    if should_clear_screen:
        lcd.clear()

    lcd.move_to(0, line)
    lcd.putstr(str)

    sleep(delay)


def get_pot_wh(pot_reading, intervalo):

    TENSÃO_MÁXIMA = 6.0
    CORRENTE_SIMULADA = 0.05
    FATOR_ESCALA = 10000000 # temos que ampliar a escala pois o potenciometro
                            #  nos da uma potencia extremamente baixa

    proporcao = pot_reading / 65535
    tensao = proporcao * TENSÃO_MÁXIMA

    if tensao < 0.05:
        tensao = 0

    corrente = CORRENTE_SIMULADA
    potencia = tensao * corrente * FATOR_ESCALA

    # Energia somente do intervalo atual
    energia_wh = (potencia * intervalo) / 3600

    return energia_wh


def acender_led(led):
    led_verde.value(0)
    led_amarelo.value(0)
    led_vermelho.value(0)

    led.value(1)


def formatar_dado(dado, base):

    if base == "dec":
        return "{:.1f} Wh".format(dado)

    elif base == "hex":
        valor_wh = int(round(dado))
        return "{:X} Wh".format(valor_wh)

    elif base == "bin":
        valor_wh = int(round(dado))
        return "{:b} Wh".format(valor_wh)

    else:
        return "Base inválida"



# potenciômetro conectado ao GP26
pot_tensao = ADC(26)

# potenciômetro conectado ao GP28
pot_consumo = ADC(28)


def main():

    base = "dec"
    ultimo_tempo = ticks_ms()

    botao_decimal_bool = False
    botao_binario_bool = False
    botao_hexdecimal_bool = False

    print_to_lcd("Controle Inteligente", 0, 1, True)
    print_to_lcd("de Sessão de Recarga", 0, 1, True)
    print_to_lcd("SELECIONAR BASE", 0, 1, True)

    while True:

        # Os botoes usam PULL_UP, portanto pressionado = 0
        botao_decimal_bool = botao_decimal.value() == 0
        botao_binario_bool = botao_binario.value() == 0
        botao_hexdecimal_bool = botao_hexdecmal.value() == 0

        if botao_decimal_bool == True:
            base = "dec"
            print_to_lcd("DECIMAL", 0, 1, True)
            print_to_lcd("SELECIONADO", 1, 1, False)
            break

        elif botao_binario_bool == True:
            base = "bin"
            print_to_lcd("BINARIO", 0, 1, True)
            print_to_lcd("SELECIONADO", 1, 1, False)
            break

        elif botao_hexdecimal_bool == True:
            base = "hex"
            print_to_lcd("HEXADECIMAL", 0, 1, True)
            print_to_lcd("SELECIONADO", 1, 1, False)
            break

        sleep(0.05)

    while True:

        agora = ticks_ms()
        intervalo_ms = ticks_diff(agora, ultimo_tempo)
        ultimo_tempo = agora
        intervalo_segundos = intervalo_ms / 1000

        botao_decimal_bool = botao_decimal.value() == 0
        botao_binario_bool = botao_binario.value() == 0
        botao_hexdecimal_bool = botao_hexdecmal.value() == 0

        leitura_geracao = pot_tensao.read_u16()
        leitura_consumo = pot_consumo.read_u16()

        energia_gerada = get_pot_wh(leitura_geracao, intervalo_segundos)

        energia_consumida = get_pot_wh(leitura_consumo, intervalo_segundos)

        energia_disponivel = energia_gerada - energia_consumida

        energ_ger_str = formatar_dado(energia_gerada, base)
        energ_con_str = formatar_dado(energia_consumida, base)
        energ_dis_str = formatar_dado(energia_disponivel, base)

        print_to_lcd("Energ. gerada", 0, 1, True)
        print_to_lcd(energ_ger_str, 1, 1, False)

        print_to_lcd("Energ. consumida", 0, 1, True)
        print_to_lcd(energ_con_str, 1, 1, False)

        print_to_lcd("Ener. Disponivel", 0, 1, True)
        print_to_lcd(energ_dis_str, 1, 1, False)
        estado_recarga = ""

        #energia_disponivel *= 1000 #
        if energia_disponivel < 0:

            acender_led(led_vermelho)
            estado_recarga = "BLOQUEADA"

        elif energia_disponivel < 600:

            acender_led(led_amarelo)
            estado_recarga = "REDUZIDA"

        else:

            acender_led(led_verde)
            estado_recarga = "AUTORIZADA"

        print_to_lcd("Recarga: ", 0, 1, True)
        print_to_lcd(estado_recarga, 1, 1, False)


main()
