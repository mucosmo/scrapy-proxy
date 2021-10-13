'''
Author: mfuture@qq.com
Date: 2021-04-22 14:28:08
LastEditTime: 2021-10-13 17:08:41
LastEditors: mfuture@qq.com
Description:
FilePath: /health39/jbk39/pipelines.py
'''
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import json
from jbk39.lib.db_service import database as db


class Jbk39Pipeline(object):

    def open_spider(self, spider):
            print('open_spider')
            # 将数据写入文件，以便查看
            self.f = open('data/scrapyItem.json', 'w', encoding='utf-8')

    def process_item(self, item, spider):
            try:
                self.f.write(json.dumps(dict(item), ensure_ascii=False))
                self.f.write('\n')
            except Exception as e:
                print(e)

            # 写入数据库保存
            if item['classify']=='diagnosis':
                    db.create_diagnosis("disease",item)
            elif item['classify']=='treat':
                    db.update_treat("disease",item)
            elif item['classify']=='intro':
                    db.create_intro("disease",item)   				
                
            return item

    def close_spider(self,spider):
            print('close_spider')
            # self.f.close()
