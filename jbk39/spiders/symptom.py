'''
Author: mfuture@qq.com
Date: 2021-10-18 09:11:34
Description: 爬取39健康网症状
FilePath: /health39/jbk39/spiders/symptom.py
'''

import scrapy
import time  # 引入time模块
import logging

from jbk39.items import Jbk39Item
import json
from jbk39.lib.common import StrFunc
import re

from jbk39.lib.service import DatabaseService as db


global count
count = 0


class jbk39(scrapy.Spider):  # 需要继承scrapy.Spider类

    name = "symptom"  # 定义蜘蛛名

    custom_settings = {
        "DOWNLOAD_DELAY": 0.2,  # 覆盖settings 里面的载延迟 ， 利用代理时本身就有较大的延迟，所以此处可以设置小一点，不用担心被封
        "JOBDIR": './jobs/{}'.format(name),
        "USE_IP_PROXY": True
    }

    # step1: 开始请求
    def start_requests(self):

        print('--start request--')


        departments = db.select_department(['fuke'])

        base_url = "https://jbk.39.net/bw/"

        for department in departments:

            # 症状链接
            pinyin = department["pinyin"]
            url = '{}{}_t2/'.format(base_url, department["pinyin"])
            meta = {"base_url": base_url, "pinyin": pinyin}
            yield scrapy.Request(url=url, meta=meta, callback=self.init_parse)

    # step2: 获取症状分页
    def init_parse(self, response):

        base_url = "{}{}_t2_p".format(
            response.meta["base_url"], response.meta["pinyin"])

        print('--init request--')

        pages = response.xpath(
            '//ul[@class="result_item_dots"]/li/span[last()-1]/a/text()')

        # 有页面数据
        if len(pages) > 0:
            pages = int(pages.extract()[0])
        else:
            pages = 1
        
        for i in range(pages):
            # step2.2: 请求某一分页
            url = "{}{}".format(base_url, str(i+1))
            yield scrapy.Request(url=url, meta=response.meta, callback=self.parse)

    # step3: 获取某一分页的所有症状
    def parse(self, response):

        print('--start parse--')

        # 获取某一页面下 某症状 子项目的 url
        elements = response.xpath('//*[@class="result_item_top_l"]')

        
        for ele in elements:
            # 该病的url，比如 "https://jbk.39.net/jxzgnmy/"

            link = ele.xpath('a/@href').extract()[0]

            # # NOTE: 综述，初始添加，先运行这里
            # yield scrapy.Request(url=link , meta=response.meta, callback=self.parse_review)

            # 症状起因
            yield scrapy.Request(url=link + 'zzqy', callback=self.parse_cause)

            # 诊断详述
            yield scrapy.Request(url=link + 'zdxs', callback=self.parse_diagnosis)

            # 检查鉴别
            yield scrapy.Request(url=link + 'jcjb', callback=self.parse_identify)

            # 就诊指南
            yield scrapy.Request(url=link + 'jzzn', callback=self.parse_patient_guide)

    # ==============================  step4: 以下均为页面解析  =============================

    # 综述
    def parse_review(self, response):
        # print('goto diagnosis_parse')
        item = Jbk39Item()

        print('综述----')

        # 疾病名称
        name = response.xpath('//div[@class="tik clearfix"]//h1/text()').extract()[0]

        intro= response.xpath('//dd[@id="intro"]/p/text()').extract()[0]

        possible_disease=[] # 可能的疾病

        elements= response.xpath('//table[@class="dis"]/tr[position()>1]')

        for ele in elements:
            possible_disease.append({
                'name':ele.xpath('./td[1]//text()').extract()[0], # 疾病名称
                'symptom':ele.xpath('./td[2]/a/text()').extract(), # 伴随症状
                'department':ele.xpath('./td[3]/a/text()').extract() # 就诊科室
                })

        item["name"] = StrFunc().str_format(name)
        item['intro'] = StrFunc().str_format(intro)
        item['possible_disease']=json.dumps(possible_disease,ensure_ascii=False)
        item['classify'] = 'symptom:intro'

        yield item

    # 症状起因
    def parse_cause(self, response):

        item = Jbk39Item()
        print('症状起因----')
        
        name = response.xpath('//div[@class="tik clearfix"]//h1/text()').extract()[0]
        cause=[]
        elements = response.xpath('//div[@class="lbox_con"]//p').extract()
        for ele in elements:
            cause.append(StrFunc().str_format(ele))
        
        item['cause'] = json.dumps(cause,ensure_ascii=False)
        item['classify'] = 'symptom:cause'
        item['name'] = name
        yield item

    # 诊断详述
    def parse_diagnosis(self, response):

        item = Jbk39Item()

        print('诊断详述----')

        name = response.xpath('//div[@class="tik clearfix"]//h1/text()').extract()[0]

        diagnosis = []

        elements = response.xpath('//div[@class="lbox_con"]//p').extract()

        for ele in elements:
            diagnosis.append(StrFunc().str_format(ele))

        item["diagnosis"] = json.dumps(diagnosis,ensure_ascii=False)
        item['classify'] = 'symptom:diagnosis'
        item['name'] = name

        yield item

    # 检查鉴别
    def parse_identify(self, response):

        item = Jbk39Item()  

        print('检查鉴别----')

        name = response.xpath('//div[@class="tik clearfix"]//h1/text()').extract()[0]

        identify = []

        elements= response.xpath('//tbody/tr[position()>1]')

        for ele in elements:
            identify.append({
                'name':ele.xpath('./td[1]//text()').extract(),  # 检查名称
                'body':ele.xpath('./td[2]//text()').extract()[0].split(' '),  # 身体部位
                'department':ele.xpath('./td[3]//text()').extract()[0].split(' '),  # 检查科室
                'affect':ele.xpath('./td[4]//text()').extract()  # 检查作用
                })

        item["identify"] = json.dumps(identify,ensure_ascii=False)
        item['classify'] = 'symptom:identify'
        item['name'] = name

        yield item

    # 就诊指南
    def parse_patient_guide(self, response):

        item = Jbk39Item()

        print('就诊指南----')

        

        name = response.xpath('//div[@class="tik clearfix"]//h1/text()').extract()[0]

        treat_guide = []

        elements = response.xpath('//div[@class="zn-main"]//dl/*/text()').extract()

        for ele in elements:
            treat_guide.append(StrFunc().str_format(ele))

        item["treat_guide"] = json.dumps(treat_guide,ensure_ascii=False)
        item['classify'] = 'symptom:treat_guide'
        item['name'] = name

        yield item


