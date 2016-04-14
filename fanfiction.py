
from scrapy import signals, Spider, Item, Field, Request
from scrapy.crawler import Crawler
from scrapy.exporters import XmlItemExporter, JsonLinesItemExporter
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Join, MapCompose, TakeFirst
from scrapy.settings import Settings
from scrapy.utils import log
from twisted.internet import reactor

from bs4 import BeautifulSoup
from w3lib.html import remove_tags
import re

class StoryItem(Item):
    title  = Field()
    author = Field()
    desc   = Field()
    body   = Field()
    url    = Field()
    site   = Field()
    theme  = Field()
    page   = Field()

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
    body_out  = Join()
    theme_out = Join(', ')

class JsonLinesExportPipeline(object):
    def __init__(self):
        self.files = {}

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        file = open('%s_products.jl' % spider.name, 'w+b')
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
        "https://www.fanfiction.net/%s/" % c for c in 
        (
            'anime',
            'book',
            'cartoon',
            'comic',
            'game',
            'misc',
            'movie',
            'play',
            'tv'
        )
    ]

    def parse(self, response):
        for href in response.xpath('//td[@valign="TOP"]/div/a/@href'):
            url = response.urljoin(href.extract())
            yield Request(url, callback = self.parse_tag)

    def parse_tag(self, response):
        for href in response.xpath('//div/center[1]/a[contains(text(), "Next")]/@href'):
            url = response.urljoin(href.extract())
            yield Request(url, callback = self.parse_tag)

        for href in response.xpath('//div[contains(@class,"z-list")]/a[1]/@href'):
            long_url = response.urljoin(href.extract())
            url      = '/'.join(long_url.split('/')[0:-1])
            yield Request(url, callback = self.parse_story)

    def parse_story(self, response):
        header  = response.xpath('//span[@class="xgray xcontrast_txt"]/text()')
        head    = header.extract()[1]
        chapter = int(response.url.split('/')[-1])
        more    = re.search('Chapters: [0-9]*', head)
        if more and chapter == 1:
            chapters = int(more.group(0).split()[1])
            base_url = '/'.join(response.url.split('/')[0:-1])
            urls = [
                base_url + '/' +  str(x) for x in range(2, chapters+1)
            ]
            for url in urls:
                yield Request(url, callback = self.parse_story)

        loader = FFItemLoader(StoryItem(), response=response)
        loader.add_xpath('title', '//*[@id="profile_top"]/b/text()')
        loader.add_xpath('author', '//*[@id="profile_top"]/a[1]/text()')
        loader.add_xpath('desc', '//*[@id="profile_top"]/div')
        loader.add_xpath('body', '//*[@id="storytext"]')
        loader.add_value('url', response.url)
        loader.add_value('site', 'fanfiction.net')
        loader.add_value('theme', '')
        loader.add_value('page', str(chapter))
        yield loader.load_item()

class LESpider(Spider):
    name = "le"
    allowed_domains = ["literotica.com"]
    start_urls = [
        "https://www.literotica.com/c/%s/1-page" % c for c in
        (
            'adult-how-to',
            'adult-humor',
            'adult-romance',
            'anal-sex-stories',
            'bdsm-stories',
            'bdsm-stories',
            'celebrity-stories',
            'chain-stories',
            'erotic-couplings',
            'erotic-horror',
            'erotic-letters',
            'erotic-novels',
            'erotic-poetry',
            'exhibitionist-voyeur',
            'fetish-stories',
            'first-time-sex-stories',
            'gay-sex-stories',
            'group-sex-stories',
            'illustrated-erotic-fiction',
            'interracial-erotic-fiction',
            'lesbian-sex-stories',
            'loving-wives',
            'masturbation-stories',
            'mature-sex',
            'mind-control',
            'non-consent-stories',
            'non-erotic-poetry',
            'non-erotic-stories',
            'non-human-stories',
            'reviews-and-essays',
            'science-fiction-fantasy',
            'taboo-sex-stories',
            'transsexuals-crossdressers'
        )
    ]

    def parse(self, response):
        for href in response.xpath('//*[@id="content"]/div/div/h3/a/@href'):
            url = response.urljoin(href.extract())
            yield Request(url, callback=self.parse_story)
        for href in response.xpath('//*[@class="b-pager-next"]/@href'):
            url = response.urljoin(href.extract())
            yield Request(url, callback=self.parse)

    def parse_story(self, response):
        for href in response.xpath('//*[@class="b-pager-next"]/@href'):
            url = response.urljoin(href.extract())
            yield Request(url, callback=self.parse_story)

        loader = StoryItemLoader(StoryItem(), response=response)
        loader.add_xpath('title', '//h1/text()')
        loader.add_xpath('author', '//*[@id="content"]/div[2]/span[1]/a/text()')
        loader.add_value('desc', '')
        loader.add_xpath('theme', ('//*[@id="content"]/div[1]/a/text()'))
        loader.add_xpath('body', '//*[@id="content"]/div[3]/div')
        loader.add_value('url', response.url)
        loader.add_value('site', 'literotica.com')
        loader.add_xpath('page', '//*[@class="b-pager-active"]/text()')
        yield loader.load_item()

class AOSpider(Spider):
    name = "ao"
    allowed_domains = ["archiveofourown.org"]
    start_urls = [
        "https://archiveofourown.org/media"
    ]

    def parse(self, response):
        for href in response.xpath('//h3/a/@href'):
            url = response.urljoin(href.extract())
            yield Request(url, callback=self.parse_genre)

    def parse_genre(self, response):
        for href in response.xpath('//li/ul/li/a/@href'):
            url = response.urljoin(href.extract())
            yield Request(url, callback=self.parse_tag)
        

    def parse_tag(self, response):
        for href in response.xpath('(//ol[@role="navigation"])[1]/li[last()]/a/@href'):
            url = response.urljoin(href.extract())
            yield Request(url, callback=self.parse_tag)

        for href in response.xpath('//h4/a[1]/@href'):
            url = response.urljoin(href.extract()) + '?view_full_work=true&view_adult=true'
            yield Request(url, callback=self.parse_story)

    def parse_story(self, response):
        loader = AOItemLoader(StoryItem(), response=response)
        loader.add_xpath('title', '//h2/text()')
        loader.add_xpath('author', '//a[@rel="author"]/text()')
        loader.add_xpath('desc', '(//*[@class="summary module"])[1]//p/text()')
        loader.add_xpath('body', '//*[@id="chapters"]//div/p/text()')
        loader.add_value('url', response.url)
        loader.add_value('site', 'archiveofourown.org')
        loader.add_xpath('theme', '//dd[@class="fandom tags"]//a/text()')
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
le_spider = LESpider()
ao_spider = AOSpider()

# instantiate a crawler passing in settings
# crawler = Crawler(settings)
ff_crawler = Crawler(ff_spider, settings)
le_crawler = Crawler(le_spider, settings)
ao_crawler = Crawler(ao_spider, settings)
# configure signals
ff_crawler.signals.connect(callback, signal=signals.spider_closed)
le_crawler.signals.connect(callback, signal=signals.spider_closed)
ao_crawler.signals.connect(callback, signal=signals.spider_closed)

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