# -*- coding: utf-8 -*-    
from src.logger import logger, loggerMapClicked
from cv2 import cv2
from os import listdir
from random import randint
from random import random
from pyclick import HumanClicker
from datetime import datetime
from numpy import asarray

import numpy as np
import mss
import pyautogui
import time
import sys
import yaml
import telegram
import os

hc = HumanClicker()
pyautogui.MINIMUM_DURATION = 0.1
pyautogui.MINIMUM_SLEEP = 0.1
pyautogui.PAUSE = 2
TELEGRAM_BOT_TOKEN = "Token API"
TELEGRAM_CHAT_ID  = "Chat ID"
CONTA = "Conta 1"

bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)


def telegram_bot_sendtext(bot_message, num_try=0):
    global bot
    try:
        return bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=bot_message)
    except:
        if num_try == 1:
            bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
            return telegram_bot_sendtext(bot_message, 1)
        return 0

def telegram_bot_sendphoto(photo_path, num_try=0):
    global bot
    try:
        return bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=open(photo_path, "rb"))
    except:
        if num_try == 1:
            bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
            return telegram_bot_sendphoto(photo_path, 1)
        return 0

test = telegram_bot_sendtext("🔌 Bot inicializado na " + CONTA + ". \n\n 💰 É hora de faturar alguns BCoins!!!")

saldo_atual = 0.0

if __name__ == '__main__':
    stream = open("config.yaml", 'r')
    c = yaml.safe_load(stream)

ct = c['threshold']
ch = c['home']

pyautogui.PAUSE = c['time_intervals']['interval_between_moviments']

cat = """
>>---> BOT original do https://github.com/mpcabete/bombcrypto-bot/

>>---> Modificações por RZancA

>>---> Pressione ctrl + c para parar o BOT.

>>---> As configurações variáveis estão em config.yaml"""

def addRandomness(n, randomn_factor_size=None):
    if randomn_factor_size is None:
        randomness_percentage = 0.1
        randomn_factor_size = randomness_percentage * n

    random_factor = 2 * random() * randomn_factor_size
    if random_factor > 5:
        random_factor = 5
    without_average_random_factor = n - randomn_factor_size
    randomized_n = int(without_average_random_factor + random_factor)
    return int(randomized_n)

def moveToWithRandomness(x,y,t):
    hc.move((int(x), int(y)), t)

def remove_suffix(input_string, suffix):
    if suffix and input_string.endswith(suffix):
        return input_string[:-len(suffix)]
    return input_string

def load_images():
    file_names = listdir("./targets/")
    targets = {}
    for file in file_names:
        path = "targets/" + file
        targets[remove_suffix(file, ".png")] = cv2.imread(path)

    return targets

images = load_images()

def loadHeroesToSendHome():
    file_names = listdir('./targets/heroes-to-send-home')
    heroes = []
    for file in file_names:
        path = './targets/heroes-to-send-home/' + file
        heroes.append(cv2.imread(path))

    print('>>---> %d heroes that should be sent home loaded' % len(heroes))
    return heroes

def show(rectangles, img = None):
    if img is None:
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            img = np.array(sct.grab(monitor))
    for (x, y, w, h) in rectangles:
        cv2.rectangle(img, (x, y), (x + w, y + h), (255,255,255,255), 2)
    cv2.imshow('img',img)
    cv2.waitKey(0)

def clickBtn(img, name=None, timeout=3, threshold=ct["default"]):
    logger(None, progress_indicator=True)
    if not name is None:
        pass
    start = time.time()
    clicked = False
    while not clicked:
        matches = positions(img, threshold=threshold)
        if len(matches) == 0:
            hast_timed_out = time.time() - start > timeout
            if hast_timed_out:
                if not name is None:
                    pass
                return False
            continue

        x, y, w, h = matches[0]
        pos_click_x = x + w / 2
        pos_click_y = y + h / 2
        moveToWithRandomness(pos_click_x, pos_click_y, 1)
        pyautogui.click()
        return True

def printSreen():
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        sct_img = np.array(sct.grab(monitor))
        return sct_img[:,:,:3]

def positions(target, threshold=ct['default'],img = None):
    if img is None:
        img = printSreen()
    result = cv2.matchTemplate(img,target,cv2.TM_CCOEFF_NORMED)
    w = target.shape[1]
    h = target.shape[0]

    yloc, xloc = np.where(result >= threshold)

    rectangles = []
    for (x, y) in zip(xloc, yloc):
        rectangles.append([int(x), int(y), int(w), int(h)])
        rectangles.append([int(x), int(y), int(w), int(h)])

    rectangles, weights = cv2.groupRectangles(rectangles, 1, 0.2)
    return rectangles

def scroll():

    commoms = positions(images['commom-text'], threshold = ct['commom'])
    if (len(commoms) == 0):
        return
    x,y,w,h = commoms[len(commoms)-1]

    moveToWithRandomness(x,y,1)

    if not c['use_click_and_drag_instead_of_scroll']:
        pyautogui.scroll(-c['scroll_size'])
    else:
        pyautogui.dragRel(0,-c['click_and_drag_amount'],duration=1, button='left')

def clickButtons():
    buttons = positions(images['go-work'], threshold=ct['go_to_work_btn'])
    for (x, y, w, h) in buttons:
        moveToWithRandomness(x+(w/2),y+(h/2),1)
        pyautogui.click()
        global hero_clicks
        hero_clicks = hero_clicks + 1
        if hero_clicks > 20:
            logger('⚠️ Houve muitos cliques em herois, tente aumentar o go_to_work_btn threshold')
            return
    return len(buttons)

def isHome(hero, buttons):
    y = hero[1]

    for (_,button_y,_,button_h) in buttons:
        isBelow = y < (button_y + button_h)
        isAbove = y > (button_y - button_h)
        if isBelow and isAbove:
            return False
    return True

def isWorking(bar, buttons):
    y = bar[1]

    for (_,button_y,_,button_h) in buttons:
        isBelow = y < (button_y + button_h)
        isAbove = y > (button_y - button_h)
        if isBelow and isAbove:
            return False
    return True

def clickGreenBarButtons():
    offset = 140

    green_bars = positions(images['green-bar'], threshold=ct['green_bar'])
    logger('🟩 %d Barras verdes detectadas' % len(green_bars))
    buttons = positions(images['go-work'], threshold=ct['go_to_work_btn'])
    logger('🆗 %d Botoes detectados' % len(buttons))

    not_working_green_bars = []
    for bar in green_bars:
        if not isWorking(bar, buttons):
            not_working_green_bars.append(bar)
    if len(not_working_green_bars) > 0:
        logger('🆗 %d Botoes com barra verde detectados' % len(not_working_green_bars))
        logger('👆 Clicando em %d herois' % len(not_working_green_bars))

    hero_clicks_cnt = 0
    for (x, y, w, h) in not_working_green_bars:
        moveToWithRandomness(x+offset+(w/2),y+(h/2),1)
        pyautogui.click()
        global hero_clicks
        hero_clicks = hero_clicks + 1
        hero_clicks_cnt = hero_clicks_cnt + 1
        if hero_clicks_cnt > 20:
            logger('⚠️ Houve muitos cliques em herois, tente aumentar o go_to_work_btn threshold')
            return        
    return len(not_working_green_bars)

def clickFullBarButtons():
    offset = 100
    full_bars = positions(images['full-stamina'], threshold=ct['default'])
    buttons = positions(images['go-work'], threshold=ct['go_to_work_btn'])

    not_working_full_bars = []
    for bar in full_bars:
        if not isWorking(bar, buttons):
            not_working_full_bars.append(bar)

    if len(not_working_full_bars) > 0:
        logger('👆 Clicando em %d herois' % len(not_working_full_bars))

    for (x, y, w, h) in not_working_full_bars:
        moveToWithRandomness(x+offset+(w/2),y+(h/2),1)
        pyautogui.click()
        global hero_clicks
        hero_clicks = hero_clicks + 1

    return len(not_working_full_bars)

def goToHeroes():
    if clickBtn(images['go-back-arrow']):
        global login_attempts
        login_attempts = 0

    time.sleep(1)
    clickBtn(images['hero-icon'])
    time.sleep(randint(1,3))

def goToGame():
    clickBtn(images['x'])

    clickBtn(images['treasure-hunt-icon'])

def refreshHeroesPositions():

    logger('🔃 Atualizando posicao dos herois')
    clickBtn(images['go-back-arrow'])
    clickBtn(images['treasure-hunt-icon'])

def login():
    global login_attempts
    logger('😿 Checando se o jogo se desconectou')

    if login_attempts > 3:
        logger('🔃 Muitas tentativas de login, atualizando')
        login_attempts = 0
        pyautogui.hotkey('ctrl','f5')
        return

    if clickBtn(images['connect-wallet'], timeout = 10):
        logger('🎉 Botao de conexao da carteira encontrado, logando!')
        login_attempts = login_attempts + 1
       
    if clickBtn(images['select-wallet-2'], timeout=8):
        login_attempts = login_attempts + 1
        if clickBtn(images['treasure-hunt-icon'], timeout = 15):
            login_attempts = 0
        return
        
    if not clickBtn(images['select-wallet-1-no-hover'], ):
        if clickBtn(images['select-wallet-1-hover'], threshold = ct['select_wallet_buttons'] ):
            pass
    else:
        pass

    if clickBtn(images['select-wallet-2'], timeout = 20):
        login_attempts = login_attempts + 1
        if clickBtn(images['treasure-hunt-icon'], timeout=25):
            login_attempts = 0

    if clickBtn(images['ok'], timeout=5):
        pass

def sendHeroesHome():
    if not ch['enable']:
        return
    heroes_positions = []
    for hero in home_heroes:
        hero_positions = positions(hero, threshold=ch['hero_threshold'])
        if not len (hero_positions) == 0:
            hero_position = hero_positions[0]
            heroes_positions.append(hero_position)

    n = len(heroes_positions)
    if n == 0:
        print('No heroes that should be sent home found.')
        return
    print(' %d heroes that should be sent home found' % n)
    go_home_buttons = positions(images['send-home'], threshold=ch['home_button_threshold'])
    go_work_buttons = positions(images['go-work'], threshold=ct['go_to_work_btn'])

    for position in heroes_positions:
        if not isHome(position,go_home_buttons):
            print(isWorking(position, go_work_buttons))
            if(not isWorking(position, go_work_buttons)):
                print ('hero not working, sending him home')
                moveToWithRandomness(go_home_buttons[0][0]+go_home_buttons[0][2]/2,position[1]+position[3]/2,1)
                pyautogui.click()
            else:
                print ('hero working, not sending him home(no dark work button)')
        else:
            print('hero already home, or home full(no dark home button)')

def refreshHeroes():
    logger('🏢 Procurando herois para trabalhar')

    goToHeroes()

    if c['select_heroes_mode'] == "full":
        logger('⚒️ Enviando herois com a energia cheia para o trabalho', 'green')
    elif c['select_heroes_mode'] == "green":
        logger('⚒️ Enviando herois com a energia verde para o trabalho', 'green')
    else:
        logger('⚒️ Enviando todos herois para o trabalho', 'green')

    buttonsClicked = 1
    empty_scrolls_attempts = c['scroll_attemps']

    while(empty_scrolls_attempts >0):
        if c['select_heroes_mode'] == 'full':
            buttonsClicked = clickFullBarButtons()
        elif c['select_heroes_mode'] == 'green':
            buttonsClicked = clickGreenBarButtons()
        else:
            buttonsClicked = clickButtons()

        sendHeroesHome()

        if buttonsClicked == 0:
            empty_scrolls_attempts = empty_scrolls_attempts - 1
        scroll()
        time.sleep(2)
    logger('💪 {} herois enviado para o trabalho'.format(hero_clicks))
    goToGame()

def goSaldo():
    logger('Consultando seu saldo')
    time.sleep(2)
    global saldo_atual
    clickBtn(images['consultar-saldo'])
    i = 10
    coins_pos = positions(images['coin-icon'], threshold=ct['default'])
    while(len(coins_pos) == 0):
        if i <= 0:
            break
        i = i - 1
        coins_pos = positions(images['coin-icon'], threshold=ct['default'])
        time.sleep(5)
    
    if(len(coins_pos) == 0):
        logger("Saldo não encontrado.")
        clickBtn(images['x'])
        return

    k,l,m,n = coins_pos[0]
    k = k - 44
    l = l + 130
    m = 200
    n = 50

    myScreen = pyautogui.screenshot(region=(k, l, m, n))
    img_dir = os.path.dirname(os.path.realpath(__file__)) + r'\targets\saldo1.png'
    myScreen.save(img_dir)
    time.sleep(2)
    enviar = ('🚨 Seu saldo Bcoins 🚀🚀🚀 na' + CONTA)
    test = telegram_bot_sendtext(enviar)
    telegram_bot_sendphoto(img_dir)

    clickBtn(images['x'])

def getDifference(then, now=datetime.now(), interval="horas"):

    duration = now - then
    duration_in_s = duration.total_seconds()

    yr_ct = 365 * 24 * 60 * 60  
    day_ct = 24 * 60 * 60  
    hour_ct = 60 * 60  
    minute_ct = 60

    def yrs():
        return divmod(duration_in_s, yr_ct)[0]

    def days():
        return divmod(duration_in_s, day_ct)[0]

    def hrs():
        return divmod(duration_in_s, hour_ct)[0]

    def mins():
        return divmod(duration_in_s, minute_ct)[0]

    def secs():
        return duration_in_s

    return {
        "anos": int(yrs()),
        "dias": int(days()),
        "horas": int(hrs()),
        "minutos": int(mins()),
        "segundos": int(secs()),
    }[interval]

def tempoGastoParaComletarMapa():
    try:
        data_inicio_mapa = None
        caminho = (
            os.path.dirname(os.path.realpath(__file__)) + r"\savedvars\tempo_mapa.txt"
        )
        with open(caminho, "r") as text_file:
            data_inicio_mapa = text_file.readline()
            if data_inicio_mapa == "":
                data_inicio_mapa = datetime.now()

            if not isinstance(data_inicio_mapa, datetime):
                data_inicio_mapa = datetime.strptime(
                    data_inicio_mapa, "%Y-%m-%d %H:%M:%S.%f"
                )
            intervalo = "horas"
            horas_gastas = getDifference(
                data_inicio_mapa, now=datetime.now(), interval=intervalo
            )
            if horas_gastas == 0:
                intervalo = "minutos"
                horas_gastas = getDifference(
                    data_inicio_mapa, now=datetime.now(), interval=intervalo
                )
            if horas_gastas == 0:
                intervalo = "segundos"
                horas_gastas = getDifference(
                    data_inicio_mapa, now=datetime.now(), interval=intervalo
                )

            telegram_bot_sendtext(
                f"Demoramos {horas_gastas} {intervalo} para concluir o mapa na" + CONTA + "."
            )
        with open(caminho, "w") as text_file_write:
            data_inicio_mapa = datetime.now()
            text_file_write.write(str(data_inicio_mapa))

    except:
        logger("Não conseguiu obter informações do tempo de conclusão do mapa.")
    
def main():
    global hero_clicks
    global login_attempts
    global last_log_is_progress
    hero_clicks = 0
    login_attempts = 0
    last_log_is_progress = False

    global images
    images = load_images()

    if ch['enable']:
        global home_heroes
        home_heroes = loadHeroesToSendHome()
    else:
        print('>>---> Home feature not enabled')
    print('\n')

    print(cat)
    time.sleep(5)
    t = c['time_intervals']

    last = {
    "login" : 0,
    "heroes" : 0,
    "ssaldo" :0,
    "new_map" : 0,
    #"check_for_captcha" : 0,
    "refresh_heroes" : 0
    }
    # =========

    while True:
        now = time.time()

        #if now - last["check_for_captcha"] > addRandomness(t['check_for_captcha'] * 60):
        #    last["check_for_captcha"] = now

        if now - last["heroes"] > addRandomness(t['send_heroes_for_work'] * 60):
            last["heroes"] = now
            refreshHeroes()
           
        if now - last["login"] > addRandomness(t['check_for_login'] * 60):
            sys.stdout.flush()
            last["login"] = now
            login()

        if now - last["new_map"] > t['check_for_new_map_button']:
            last["new_map"] = now

            if clickBtn(images["new-map"]):
                tempoGastoParaComletarMapa()
                loggerMapClicked()
                telegram_bot_sendtext(f"Completamos mais um mapa!")
                time.sleep(3)
                num_jaulas = len(positions(images["jail"], threshold=0.8))
                if num_jaulas > 0:
                    telegram_bot_sendtext(
                        f"Parabéns temos {num_jaulas} nova(s) jaula(s) no novo mapa 🎉🎉🎉."
                        )

        if now - last["refresh_heroes"] > addRandomness( t['refresh_heroes_positions'] * 60):
            last["refresh_heroes"] = now
            refreshHeroesPositions()
            
        if now - last["ssaldo"] > addRandomness(t['get_saldo'] * 60):
            last["ssaldo"] = now
            goSaldo()

        logger(None, progress_indicator=True)

        sys.stdout.flush()

        time.sleep(1)

main()
