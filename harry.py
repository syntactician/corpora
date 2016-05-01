from scrapy import signals, Spider, Item, Field, Request
from scrapy.crawler import Crawler
from scrapy.exporters import JsonLinesItemExporter
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Join, MapCompose, TakeFirst
from scrapy.settings import Settings
from scrapy.utils import log
from twisted.internet import reactor

from w3lib.html import remove_tags
from datetime import datetime
import re
import json

class StoryItem(Item):
    title    = Field()
    author   = Field()
    desc     = Field()
    body     = Field()
    url      = Field()
    site     = Field()
    chapter  = Field()
    category = Field()

class FFItem(StoryItem):
    id        = Field()
    rating    = Field()
    language  = Field()
    words     = Field()
    chapters  = Field()
    complete  = Field()
    comments  = Field()
    likes     = Field()
    marks     = Field()
    published = Field()
    updated   = Field()

class AOItem(FFItem):
    fandom     = Field()
    characters = Field()
    ships      = Field()
    tags       = Field()
    warnings   = Field()
    hits       = Field()

class StoryItemLoader(ItemLoader):
    default_input_processor  = MapCompose(str.strip)
    default_output_processor = TakeFirst()

    body_in  = MapCompose(remove_tags)
    body_out = Join()

class FFItemLoader(StoryItemLoader):
    # desc_out = Join()
    desc_in  = MapCompose(remove_tags)
    desc_out = Join()

class AOItemLoader(StoryItemLoader):
    body_out       = Join()
    category_out   = Join(', ')
    warnings_out   = Join(', ')
    fandom_out     = Join(', ')
    characters_out = Join(', ')
    ships_out      = Join(', ')
    tags_out       = Join(', ')

class JsonLinesExportPipeline(object):
    def __init__(self):
        self.files = {}

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(
            pipeline.spider_opened,
            signals.spider_opened
        )
        crawler.signals.connect(
            pipeline.spider_closed,
            signals.spider_closed
        )
        return pipeline

    def spider_opened(self, spider):
        file = open('%s_hp_stories.jl' % spider.name, 'w+b')
        self.files[spider] = file
        self.exporter = JsonLinesItemExporter(file)
        self.exporter.start_exporting()

    def spider_closed(self, spider):
        self.exporter.finish_exporting()
        file = self.files.pop(spider)
        file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item

class FFSpider(Spider):
    name = "ff"
    allowed_domains = ["fanfiction.net"]
    start_urls = [
        "https://www.fanfiction.net/book/Harry-Potter/"
    ]

    def parse(self, response):
        next = response.xpath(
            '//center[1]/a[contains(text(), "Next")]/@href'
        )
        for href in next:
            url = response.urljoin(href.extract())
            yield Request(url, callback = self.parse)

        stories = response.xpath(
            '//div[contains(@class,"z-list")]/a[1]/@href'
        )
        for href in stories:
            long_url = response.urljoin(href.extract())
            url      = '/'.join(long_url.split('/')[0:-1])
            yield Request(url, callback = self.parse_story)

    def parse_story(self, response):
        header  = response.xpath(
            '//span[@class="xgray xcontrast_txt"]/text()'
        )
        head    = header.extract()
        chapter = int(response.url.split('/')[-1])
        more    = re.search('Chapters: [0-9]*', head[1])

        if more and chapter == 1:
            chapters = int(more.group(0).split()[1])
            base_url = '/'.join(response.url.split('/')[0:-1])
            urls = [
                base_url + '/' +  str(x) for x in range(2, chapters+1)
            ]
            for url in urls:
                yield Request(url, callback = self.parse_story)

        time_xpath  = response.xpath(
            '//span[@data-xutime]/@data-xutime'
        )
        times       = time_xpath.extract()
        u_published = float(times[0])
        d_published = datetime.fromtimestamp(u_published)
        published   = d_published.strftime('%Y-%m-%d')
        u_updated   = float(next(reversed(times)))
        d_updated   = datetime.fromtimestamp(u_updated)
        updated     = d_updated.strftime('%Y-%m-%d')

        # info    = head[1].split(' - ')
        # language = info[1]
        # category = info[2]
        # characters = info[3]
        # words = ''.join([s for s in info[5] if s.isdigit()])

        complete = str(bool('Complete' in ' '.join(head)))

        loader = FFItemLoader(FFItem(), response=response)
        loader.add_xpath(
            'title', '//*[@id="profile_top"]/b/text()'
        )
        loader.add_xpath(
            'author', '//*[@id="profile_top"]/a[1]/text()'
        )
        loader.add_xpath(
            'desc', '//*[@id="profile_top"]/div'
        )
        loader.add_xpath(
            'body', '//*[@id="storytext"]'
        )
        loader.add_value(
            'url', response.url
        )
        loader.add_value(
            'site', 'fanfiction.net'
        )
        loader.add_value(
            'chapter', str(chapter)
        )
        loader.add_xpath(
            'rating', '//span[@class="xgray xcontrast_txt"]/a/text()'
        )
        loader.add_value(
            'published', published
        )
        loader.add_value(
            'updated', updated
        )
        yield loader.load_item()


class AOSpider(Spider):
    name = "ao"
    allowed_domains = ["archiveofourown.org"]
    start_urls = [
        "http://archiveofourown.org/tags/Harry%20Potter%20-%20J*d*%20K*d*%20Rowling/works"
    ]

    def parse(self, response):
        next = response.xpath(
            '(//ol[@role="navigation"])[1]/li[last()]/a/@href'
        )
        for href in next:
            url = response.urljoin(href.extract())
            yield Request(url, callback = self.parse)

        stories = response.xpath('//h4/a[1]/@href')
        for href in stories:
            extension = '?view_adult=true&style=disable'
            url = response.urljoin(href.extract()) + extension
            yield Request(url, callback = self.parse_story)

    def parse_story(self, response):
        next = response.xpath(
            'a[contains(text(), "Next Chapter →")]/@href'
        )
        for href in next:
            extension = '?view_adult=true&style=disable'
            url = response.urljoin(href.extract()) + extension
            yield Request(url, callback = self.parse_story)

        chapter_path   = response.xpath('//dd[@class="chapters"]/text()')
        chapters       = tuple(chapter_path.extract()[0].split('/'))
        current, total = chapters
        complete       = str(bool(current == total))

        loader = AOItemLoader(AOItem(), response = response)
        loader.add_xpath(
            'title', '//h2/text()'
        )
        loader.add_xpath(
            'author', '//a[@rel="author"]/text()'
        )
        loader.add_xpath(
            'desc', '(//*[@class="summary module"])[1]//p/text()'
        )
        loader.add_xpath(
            'body', '//*[@id="chapters"]//div/p/text()'
        )
        loader.add_value(
            'url', response.url
        )
        loader.add_value(
            'site', 'archiveofourown.org'
        )
        loader.add_xpath(
            'category', '//dd[@class="category tags"]//a/text()'
        )
        loader.add_xpath(
            'language', '//dd[@class="language"]/text()'
        )
        loader.add_xpath(
            'rating', '//dd[@class="rating tags"]//a/text()'
        )
        loader.add_xpath(
            'warnings', '//dd[@class="warning tags"]//a/text()'
        )
        loader.add_xpath(
            'fandom', '//dd[@class="fandom tags"]//a/text()'
        )
        loader.add_xpath(
            'characters', '//dd[@class="character tags"]//a/text()'
        )
        loader.add_xpath(
            'ships', '//dd[@class="relationship tags"]//a/text()'
        )
        loader.add_xpath(
            'tags', '//dd[@class="freeform tags"]//a/text()'
        )
        loader.add_xpath(
            'hits', '//dd[@class="hits"]/text()'
        )
        loader.add_xpath(
            'published', '//dd[@class="published"]/text()'
        )
        loader.add_xpath(
            'updated', '//dd[@class="status"]/text()'
        )
        loader.add_xpath(
            'words', '//dd[@class="words"]/text()'
        )
        loader.add_xpath(
            'comments', '//dd[@class="comments"]/text()'
        )
        loader.add_xpath(
            'likes', '//dd[@class="kudos"]/text()'
        )
        loader.add_xpath(
            'marks', '//dd[@class="bookmarks"]/a/text()'
        )
        loader.add_xpath(
            'hits', '//dd[@class="hits"]/text()'
        )
        loader.add_value(
            'chapter', current
        )
        loader.add_value(
            'complete', complete
        )
        yield loader.load_item()

# callback fired when the spider is closed
def callback(spider, reason):
    stats = spider.crawler.stats.get_stats()  # collect/log stats?

    # stop the reactor
    reactor.stop()

# instantiate settings and provide a custom configuration
settings = Settings()
settings.set(
    'ITEM_PIPELINES', {
        '__main__.JsonLinesExportPipeline': 100,
    }
)
settings.set(
    'USER_AGENT', 'Mozilla/5.0 (Windows NT 6.3; Win64; x64)'
)

# instantiate a spider
ff_spider = FFSpider()
ao_spider = AOSpider()

# instantiate a crawler passing in settings
# crawler = Crawler(settings)
ff_crawler = Crawler(ff_spider, settings)
ao_crawler = Crawler(ao_spider, settings)
# configure signals
ff_crawler.signals.connect(
    callback, 
    signal = signals.spider_closed
)
ao_crawler.signals.connect(
    callback,
    signal = signals.spider_closed
)

# configure and start the crawler
# crawler.configure()
# crawler.crawl(spider)
ff_crawler.crawl()
# le_crawler.crawl()
# ao_crawler.crawl()

# start logging
# log.start()
log.configure_logging()

# start the reactor (blocks execution)
reactor.run()
