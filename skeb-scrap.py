#!/usr/bin/env python

import os
import shutil
import time
import urllib.request

import webvtt
from bs4 import BeautifulSoup
from mutagen.id3 import APIC, ID3, SYLT, TIT2
from mutagen.mp3 import MP3
from selenium import webdriver


OUT = '/home/user/out'
URL = 'https://skeb.jp/works?sort=date&genre=voice'
browser = webdriver.Firefox()
browser.get(URL)

page_length = browser.execute_script("window.scrollTo(0, document.body.scrollHeight);var page_length=document.body.scrollHeight;return page_length;")
match = False
while(match == False):
    count = page_length
    time.sleep(3)
    page_length = browser.execute_script("window.scrollTo(0, document.body.scrollHeight);var page_length=document.body.scrollHeight;return page_length;")
    if count == page_length:
        match = True

soup = BeautifulSoup(browser.page_source, features='lxml')
data = soup.find_all('div', {'class':'plyr__video-wrapper'})
links = dict()
for count, i in enumerate(data):
    links[count] = {
        'image_link' : i.contents[0].attrs['poster'],
        'audio_link' : i.contents[0].contents[0].attrs['src'],
        'subs_link' : i.contents[0].contents[0].contents[0].attrs['src'],
        'work_id' : i.contents[0].contents[0].attrs['src'].split('/')[4]
    }

archive_file = 'archive.txt'
audio = 'audio.mp3'
image = 'image.png'
subs = 'subs.vtt'

try:
    with open(archive_file) as f:
        archive = f.read().splitlines()
except FileNotFoundError:
    archive = list()

for count in range(0, len(links)):
    if links[count]['work_id'] in archive:
        print('Work ID ' + links[count]['work_id'] + ' already downloaded.')
    else:
        print('Downloading work ID ' + links[count]['work_id'] + '...')
        browser.get('https://skeb.jp/works/' + links[count]['work_id'])
        soup = BeautifulSoup(browser.page_source, features='lxml')

        try:
            links[count]['author'] = soup.find('div', {'class':'subtitle'}).text[1:]
            name = links[count]['author'] + '_' + links[count]['work_id']
        except AttributeError:
            name = links[count]['work_id']

        urllib.request.urlretrieve(links[count]['audio_link'], audio)
        no_cover = False
        try:
            urllib.request.urlretrieve(links[count]['image_link'], image)
        except urllib.error.HTTPError:
            no_cover = True
        urllib.request.urlretrieve(links[count]['subs_link'], subs)

        vtt = webvtt.read(subs)
        lyrics = list()
        for string in vtt:
            times = [int(x) for x in string.start.replace('.', ':').split(':')]
            ms = times[-1] + 1000 * times[-2] + 1000 * 60 * times[-3] + 1000 * 60 *60 * times[-4]
            lyrics.append((string.text, ms))

        mp3 = MP3(audio)
        mp3.delete()
        mp3.tags = ID3()
        mp3.tags.add(TIT2(encoding=3, text=name))
        if no_cover == False:
            mp3.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, data=open(image, 'rb').read()))
        mp3.tags.add(SYLT(encoding=3, lang='jpn', text=lyrics))
        mp3.tags.save(audio)

        base_dir = os.path.dirname(__file__)
        out_dir = os.path.join(base_dir, OUT)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        shutil.move(audio, out_dir + '/' + name + '.mp3')
        if no_cover == False:
            os.remove(image)
        os.remove(subs)

        archive.append(links[count]['work_id'])
        with open(archive_file, 'w') as f:
            for item in archive:
                f.write("%s\n" % item)
