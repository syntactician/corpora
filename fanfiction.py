import sys  

reload(sys)  
sys.setdefaultencoding('utf8')

from chatterbot import ChatBot
from datetime import datetime
from glob import glob
from json import loads
from nltk import ConditionalFreqDist
from nltk import FreqDist
from nltk.corpus import stopwords
from nltk.data import load
from nltk.tokenize import word_tokenize
from scrapy import Field
from scrapy import Item
from scrapy import Request
from scrapy import Spider
from scrapy import signals
from scrapy.crawler import Crawler
from scrapy.exporters import JsonLinesItemExporter
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Join
from scrapy.loader.processors import MapCompose
from scrapy.loader.processors import TakeFirst
from scrapy.settings import Settings
from scrapy.utils import log
from string import strip
from twisted.internet import reactor
from w3lib.html import remove_tags
import json
import re


stop = stopwords.words('english')
tokenizer = load('tokenizers/punkt/english.pickle')

# real

real_chapters = []
real_words    = []
dir = 'hp'

for path in glob("hp/*.txt"):
        # soup = BeautifulSoup(open(path))
        # chapter = soup.findAll(text=True)[0]
        file = open(path)
        chapter = file.read()
        chapter_tuple = (chapter, 'real')

        words = [ w.lower() for w in word_tokenize(chapter) ]

        real_chapters.append(chapter_tuple)
        real_words.extend(words)

word_total  = len(real_words)
harry_total = real_words.count('harry')

fd = FreqDist(real_words)
fd.plot(26)

# filtered_real_words = [ w.lower() for w in real_words if w.isalpha() ]
filtered_real_words = [ w for w in real_words if w.isalpha() and w not in stop ]

Rowling = filtered_real_words

fd  = FreqDist(filtered_real_words)
fd.plot(26)

file = open('ao_hp_stories.jl')

ao_chapters = []
ao_words    = []
AO3         = []
AO3_normed  = []

for line in file.readlines():
    chapter_obj = loads(line)
    if chapter_obj['language'] == 'English':
        try:
            chapter = chapter_obj['body']
            chapter_tuple = (chapter, 'fake')
            words = [ w.lower() for w in word_tokenize(chapter) ]
            ao_words.extend(words)
            ao_chapters.append(chapter_tuple)
            if len(AO3) < word_total:
                AO3.extend(words)
            if AO3_normed.count('harry') < harry_total:
                AO3_normed.extend(words)
        except:
            pass

# i = 1100
# for line in file.readlines():
#     if i > 0:
#         chapter_obj = loads(line)
#         if chapter_obj['language'] == 'English':
#             try:
#                 chapter = chapter_obj['body']
#                 chapter_tuple = (chapter, 'fake')
#                 words = word_tokenize(chapter)
#                 ao_words.extend(words)
#                 ao_chapters.append(chapter_tuple)
#                 AO3.extend(words)
#             except:
#                 pass
#     i += 1

fd = FreqDist(ao_words)
fd.plot(26)

# filtered_ao_words = [ w.lower() for w in ao_words if w.isalpha() ]
filtered_ao_words = [ w for w in ao_words if w.isalpha() and w not in stop ]

fd = FreqDist(filtered_ao_words)
fd.plot(26)

file = open('ff_hp_stories.jl')

ff_chapters       = []
ff_words          = []
fanfiction        = []
fanfiction_normed = []

# i = 950
for line in file.readlines():
    chapter_obj = loads(line)
    try:
        chapter = chapter_obj['body']
        chapter_tuple = (chapter, 'fake')
        words = [ w.lower() for w in word_tokenize(chapter) ]
        ff_words.extend(words)
        ff_chapters.append(chapter_tuple)
        if len(fanfiction) < word_total:
            fanfiction.extend(words)
        if fanfiction_normed.count('harry') < harry_total:
            fanfiction_normed.extend(words)
    except:
        pass

# i = 950
# for line in file.readlines():
#     if i > 0:
#         chapter_obj = loads(line)
#         try:
#             chapter = chapter_obj['body']
#             chapter_tuple = (chapter, 'fake')
#             words = word_tokenize(chapter)
#             ff_words.extend(words)
#             ff_chapters.append(chapter_tuple)
#             fanfiction.extend(words)
#         except:
#             pass
#         i -= 1

fd = FreqDist(ff_words)
fd.plot(26)

ff_stop = stop
for language in ('spanish', 'portuguese', 'french'):
    ff_stop.extend(
        stopwords.words(language)
    )

# filtered_ff_words = [ w.lower() for w in ff_words if w.isalpha() ]
filtered_ff_words = [ w for w in ff_words if w.isalpha() and w not in ff_stop ]

fd = FreqDist(filtered_ff_words)
fd.plot(26)

immortal_chapters = []
immortal_words    = []

for path in glob("immortal/*.txt"):
        file = open(path)
        chapter = file.read()
        chapter_tuple = (chapter, 'real')

        words = [ w.lower() for w in word_tokenize(chapter) ]

        immortal_chapters.append(chapter_tuple)
        immortal_words.extend(words)

fd = FreqDist(immortal_words)
fd.plot(26)

# filtered_immortal_words = [ w.lower() for w in immortal_words if w.isalpha() ]
filtered_immortal_words = [ w for w in immortal_words if w.isalpha() and w not in stop ]


fd  = FreqDist(filtered_immortal_words)
fd.plot(26)

i_stop = [
    'da',
    'dat',
    'u',
    'ur',
    'wif',
    'wuz',
    'chapter'
]

# filtered_immortal_words = [ w.lower() for w in immortal_words if w.isalpha() ]
filtered_immortal_words = [ w for w in immortal_words if w.isalpha() and w not in stop and w not in i_stop ]

immortal_scale = int(len(real_words) / len(immortal_words))

My_Immortal = immortal_words * immortal_scale

fd  = FreqDist(filtered_immortal_words)
fd.plot(26)

names = (
    'neville',
    'draco',
    'dumbledore',
    'fred',
    'george',
    'ginny',
    'harry',
    'hermione',
    'james',
    'lily',
    'luna',
    'lupin',
    'malfoy',
    'pansy',
    'potter',
    'remus',
    'ron',
    'severus',
    'sirius',
    'snape',
    'weasley'
)

AO3 = [ w.lower() for w in AO3 if w.isalpha() ]
AO3 = [ w for w in AO3 if w not in stop ]

fanfiction = [ w.lower() for w in fanfiction if w.isalpha() ]
fanfiction = [ w for w in fanfiction if w not in stop ]

My_Immortal = [ w.lower() for w in My_Immortal if w.isalpha() ]
My_Immortal = [ w for w in My_Immortal if w not in stop and w not in i_stop]

unified_words = (
    (source, word)
    for source in (
        'Rowling',
        'AO3',
        'fanfiction',
        'My_Immortal'
    )
    for word in eval(source)
    if word in names
)

cfd = ConditionalFreqDist(unified_words)

cfd.plot()

# AO3_normed = [ w.lower() for w in AO3_normed if w.isalpha() ]
# AO3_normed = [ w for w in AO3_normed if w not in stop ]

# fanfiction_normed = [ w.lower() for w in fanfiction_normed if w.isalpha() ]
# fanfiction_normed = [ w for w in fanfiction_normed if w not in stop ]

unified_words = (
    (source, word)
    for source in (
        'Rowling',
        'AO3_normed',
        'fanfiction_normed'
    )
    for word in eval(source)
	if word in names
)
cfd = ConditionalFreqDist(unified_words)
cfd.plot()

chatbot = ChatBot(
    "Mary Sue",
    io_adapter = "chatterbot.adapters.io.NoOutputAdapter"
)
# chatbot.train("chatterbot.corpus.english")

file = open('le_products.jl')

for line in file.readlines():
    conversation = []
    story = json.loads(line)
    body = story['body']
    graphs = body.split('\n')
    for graph in graphs:
        speech = graph.split('"')[1::2]
        utterance = ' '.join(speech)
        if utterance:
            conversation.append(utterance)
    if conversation:
        chatbot.train(conversation)

print(
    chatbot.get_response("Hello")
)
