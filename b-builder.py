import urllib.parse
import datetime
import glob
import os
import sys
import math
import shutil
from PIL import Image, ImageFont, ImageDraw
import cv2
import numpy as np

INDEX_NUMBER_OF_DISPLAY_ARTICLES = 20

#Build Settings
BLOG_ROOT_URL = 'https://it.sakai-sc.co.jp/'
OG_IMAGE_BASE = 'og-image-base.png'
OG_IMAGE_FONT_FILE = 'GenShinGothic-Bold.ttf'
PICKUP_TAGS = ['IT活用経営', '経営コンサルティング', 'プログラミング', '論説']
PUSH_CONTACT_TAGS = ['IT活用経営', '経営コンサルティング', '論説']

#directory names
OUTPUT_OUTPUT_DIRECTORY_NAME = 'output'
OUTPUT_ARTICLE_DIRECTORY_NAME = 'article'
OUTPUT_SEARCH_DIRECTORY_NAME = 'article'
OUTPUT_IMAGE_DIRECTORY_NAME = 'image'
OUTPUT_OG_IMAGE_DIRECTORY_NAME = 'og-images'
PANKUZU_HOME_DISPLAY_TEXT = 'ホーム'

DESCRIPTION_LENGTH = 100

MARKDOWN_CODE_FLAG = '```'

WRAPPER = '\n'
tag_ens = {}

#static file origin items
_build_root_path = sys.argv[1]
#reading static files
_amazon_links = {}
with open(_build_root_path + '/pickup-articles.txt', 'r', encoding='UTF-8') as f:
    _pickup_article_names = f.read().split('\n')
with open(_build_root_path + '/common_parts/google_ad_vertical.txt', 'r', encoding='UTF-8') as f:
    _google_ad_vertical = f.read()
with open(_build_root_path + '/common_parts/aside-banners.html', 'r', encoding='UTF-8') as f:
    _aside_banners = f.read()
for amazon_link_file_base in glob.glob(f'{_build_root_path}/common_parts/Amazon/*'):
    amazon_link_file = amazon_link_file_base.replace('\\', '/')
    tag_name = os.path.basename(amazon_link_file).split('.')[0]
    with open(amazon_link_file, 'r', encoding='UTF-8') as f:
        _amazon_links[tag_name] = f.read()
with open(_build_root_path + '/common_parts/google_ad_inline.txt', 'r', encoding='UTF-8') as f:
    _google_ad_inline = f.read()

def main():
    build(_build_root_path)

def build(build_root_path):
    if build_root_path.endswith('/'):
        build_root_path = build_root_path[:len(build_root_path) - 1]
    _PartsBuilder.remove_before_run(build_root_path)
    output_directory_path = '{}/{}'.format(build_root_path, OUTPUT_OUTPUT_DIRECTORY_NAME)
    with open(build_root_path + '/tag_en.txt', 'r', encoding='UTF-8') as f:
        for line in f.read().split('\n'):
            if line.startswith('#'):
                continue
            kv = line.split('\t')
            tag_ens[kv[0]] = kv[1].lower()

    if not os.path.exists(output_directory_path):
        os.makedirs(output_directory_path)
    if not os.path.exists(output_directory_path + '/' + OUTPUT_ARTICLE_DIRECTORY_NAME):
        os.makedirs(output_directory_path + '/' + OUTPUT_ARTICLE_DIRECTORY_NAME)
    if not os.path.exists(output_directory_path + '/' + OUTPUT_SEARCH_DIRECTORY_NAME):
        os.makedirs(output_directory_path + '/' + OUTPUT_SEARCH_DIRECTORY_NAME)

    header = _PartsBuilder.get_html_from_second_line_to_end(build_root_path + '/common_parts/header.html')
    footer = _PartsBuilder.get_html_from_second_line_to_end(build_root_path + '/common_parts/footer.html')
    head_infomation_map = _PartsBuilder.get_head_infomation_map(build_root_path)

    #article files
    article_list_wrapper = ArticleListWrapper(build_root_path=build_root_path)

    #build article pages
    article_list_wrapper.save_article_files(head_infomation_map=head_infomation_map, header=header, footer=footer, output_directory_path=output_directory_path)

    #index file
    breadcrumbs_href_value__tag__map_list = []
    breadcrumbs_href_value__tag__map_list.append({'href_value':None, 'tag':PANKUZU_HOME_DISPLAY_TEXT})
    breadcrumbs_href_value__tag__map_list_for_list_page = []
    breadcrumbs_href_value__tag__map_list_for_list_page.append({'href_value':BLOG_ROOT_URL, 'tag':PANKUZU_HOME_DISPLAY_TEXT})
    breadcrumbs_href_value__tag__map_list_for_list_page.append({'href_value':None, 'tag':None})
    target_articles = []
    page_index = 1

    #aside parts
    aside_for_index = _PartsBuilder.get_aside_html(article_list_wrapper, build_root_path)

    for i in range(len(article_list_wrapper._articles)):
        target_articles.append(article_list_wrapper._articles[i])
        if len(target_articles) == INDEX_NUMBER_OF_DISPLAY_ARTICLES or i + 1 == len(article_list_wrapper._articles):
            if page_index == 1:
                display_title = '新着記事'
                display_range_text = f'全{len(article_list_wrapper._articles)}記事の内、新着{INDEX_NUMBER_OF_DISPLAY_ARTICLES}件の記事を表示中'
                page_category = _PageCategory.INDEX
                bread = breadcrumbs_href_value__tag__map_list
            else:
                index_from = f'{(page_index - 1) * INDEX_NUMBER_OF_DISPLAY_ARTICLES + 1}'
                index_to = f'{(page_index - 1) * INDEX_NUMBER_OF_DISPLAY_ARTICLES + len(target_articles)}'
                display_title = f'{index_from}～{index_to}番目の記事（新着順）'
                display_range_text = f'{display_title}を表示中'
                page_category = _PageCategory.ARTICLE_LIST_WITH_INDEX
                breadcrumbs_href_value__tag__map_list_for_list_page[len(breadcrumbs_href_value__tag__map_list_for_list_page) - 1]['tag'] = f'記事一覧（{index_from}～{index_to}番目の記事）'
                bread = breadcrumbs_href_value__tag__map_list_for_list_page
            html = _PartsBuilder.build_index_or_search_html(build_root_path, head_infomation_map=head_infomation_map, articles=target_articles, header=header, aside=aside_for_index, footer=footer, display_title=display_title, page_category=page_category, breadcrumbs_href_value__tag__map_list=bread, page_index=page_index, total_number_of_index_pages=article_list_wrapper.get_total_number_of_index_pages(), display_range_text=display_range_text)
            if page_index == 1:
                save_path = f'{output_directory_path}/index.html'
            else:
                save_path = f'{output_directory_path}/{OUTPUT_ARTICLE_DIRECTORY_NAME}/{page_index}.html'
            with open(save_path, mode="w", encoding='UTF-8') as f:
                f.write(html)
            page_index += 1
            target_articles = []

    #all-articles file
    breadcrumbs_href_value__tag__map_list = []
    breadcrumbs_href_value__tag__map_list.append({'href_value':BLOG_ROOT_URL, 'tag':PANKUZU_HOME_DISPLAY_TEXT})
    breadcrumbs_href_value__tag__map_list.append({'href_value':None, 'tag':'記事一覧'})
    html = _PartsBuilder.build_index_or_search_html(build_root_path, head_infomation_map=head_infomation_map, articles=article_list_wrapper._articles, header=header, aside=aside_for_index, footer=footer, display_title='全記事一覧', page_category=_PageCategory.ARTICLE_LIST, breadcrumbs_href_value__tag__map_list=breadcrumbs_href_value__tag__map_list)
    with open(f'{output_directory_path}/{OUTPUT_ARTICLE_DIRECTORY_NAME}/index.html', mode="w", encoding='UTF-8') as f:
        f.write(html)

    #build search files
    for tag, articles_with_the_tag in article_list_wrapper._tag_articles_map.items():
        breadcrumbs_href_value__tag__map_list = []
        breadcrumbs_href_value__tag__map_list.append({'href_value':BLOG_ROOT_URL, 'tag':PANKUZU_HOME_DISPLAY_TEXT})
        breadcrumbs_href_value__tag__map_list.append({'href_value':None, 'tag':tag})

        tag_en = _PartsBuilder.get_tag_en(tag)
        tag_escaped = _PartsBuilder.tag_escaping(tag_en)
        save_dir = "{}/{}/{}".format(output_directory_path, OUTPUT_SEARCH_DIRECTORY_NAME, tag_escaped)
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        html = _PartsBuilder.build_index_or_search_html(build_root_path, head_infomation_map=head_infomation_map, articles=articles_with_the_tag, header=header, aside=aside_for_index, footer=footer, display_title=f'{tag} を含む記事の一覧', page_category=_PageCategory.SEARCH, breadcrumbs_href_value__tag__map_list=breadcrumbs_href_value__tag__map_list)
        with open(f'{save_dir}/index.html', mode="w", encoding='UTF-8') as f:
            f.write(html)

    #og-images
    for article in article_list_wrapper._articles:
        og_img = article.generate_og_image()
        Image.fromarray(og_img).save(f'{output_directory_path}/{article.get_og_image_save_relative_path()}')

    #build sitemap
    sitemap_content = _PartsBuilder.sitemap_builder(article_list_wrapper=article_list_wrapper)
    with open("{}/sitemap.xml".format(output_directory_path), mode="w", encoding='UTF-8') as f:
        f.write(sitemap_content)

    print(f'output terminated in {output_directory_path}.')


class ArticleListWrapper():
    def __init__(self, build_root_path):
        self._build_root_path = build_root_path
        article_html_files_path = glob.glob(build_root_path + "/articles/*.html")
        self._articles = [Article(article_file_path=x, meta_infomation_map=_PartsBuilder.get_article_mata_infomation(x.replace('.html', '.txt'))) for x in article_html_files_path]
        self._articles.sort(key=lambda x: x._post_date, reverse=True)
        self._tag_articles_map = {}
    def save_article_files(self, head_infomation_map, header, footer, output_directory_path):
        for article in self._articles:
            article.check_title()
            articles_with_same_category, category_name = self.get_article_objects_and_tag_with_same_tag(article=article)
            article.save_article_file(build_root_path=self._build_root_path, article_list_wrapper=self, head_infomation_map=head_infomation_map, header=header, footer=footer, output_directory_path=output_directory_path, articles_with_same_category=articles_with_same_category, category_name=category_name)
            for tag in article._tags:
                if tag in self._tag_articles_map:
                    self._tag_articles_map[tag].append(article)
                else:
                    self._tag_articles_map[tag] = [article]
    def get_latest_article_object(self):
        return self._articles[0]
    def get_article_objects_and_tag_with_same_tag(self, article):
        if len(article._tags) <= 1:
            return list(filter(lambda x: article._tags[0] in x._tags, self._articles)), article._tags[0]
        article_with_second_tag = list(filter(lambda x: article._tags[1] in x._tags, self._articles))
        if len(article_with_second_tag) >= 3:
            return article_with_second_tag, article._tags[1]
        else:
            return list(filter(lambda x: article._tags[0] in x._tags, self._articles)), article._tags[0]

    def get_all_tags(self):
        result = []
        for article in self._articles:
            for tag in article._tags:
                if not tag in result:
                    result.append(tag)
        return result
    def get_total_number_of_index_pages(self):
        return math.ceil(len(self._articles)/INDEX_NUMBER_OF_DISPLAY_ARTICLES)

class Article():
    def __init__(self, article_file_path, meta_infomation_map):
        self._article_file_path = article_file_path
        self._file_name = os.path.basename(self._article_file_path)
        self._meta_infomation_map = meta_infomation_map
        self._title = meta_infomation_map['article_title']
        post_date_parts = meta_infomation_map['post_date'].split('-')
        self._post_date = datetime.date(int(post_date_parts[0]), int(post_date_parts[1]), int(post_date_parts[2]))
        self._tags = meta_infomation_map["tags"].split(',')
        self._absolute_url = self.get_article_absolute_url()
        self._image_name = meta_infomation_map["article_image_filename"]
        with open(self._article_file_path, 'r', encoding='UTF-8') as f:
            self._contents = f.read()
        self._description = self._contents[:DESCRIPTION_LENGTH * 3].replace('堺です。', '').replace('こんにちは。', '').replace('こんにちは、', '').replace('お世話様です。', '').replace('\n', '').replace('<strong>', '').replace('</strong>', '')[:DESCRIPTION_LENGTH - 2] + '...'
        if 'update_date' in meta_infomation_map:
            update_date_text_split = meta_infomation_map['update_date'].split(' ')[0].split('-')
            update_time_text_split = meta_infomation_map['update_date'].split(' ')[1].split(':')
            update_date = datetime.datetime(int(update_date_text_split[0]), int(update_date_text_split[1]), int(update_date_text_split[2]), int(update_time_text_split[0]), int(update_time_text_split[1]), 0)
            if update_date.day != self._post_date.day or update_date.month != self._post_date.month or update_date.year != self._post_date.year:
                self._update_date = update_date
            else:
                self._update_date = None
    def check_title(self):
        if len(self._title) > 33:
            print(f'The article title "{self._title}" is longer than 33 chars.')

    def save_article_file(self, build_root_path, article_list_wrapper, head_infomation_map, header, footer, output_directory_path, articles_with_same_category, category_name):

        #for img test
        #og_img = self.generate_og_image()
        #Image.fromarray(og_img).save(f'C:/Users/sakai/Desktop/ewrw/{os.path.basename(self._article_file_path)}.png')

        article_build_result_text = _PartsBuilder.build_head(build_root_path, head_infomation_map=head_infomation_map, page_title='{} | {}'.format(self._title, head_infomation_map['blog_title']), page_category=_PageCategory.ARTICLE, article=self, noindex=False) + WRAPPER
        article_build_result_text += '<body>' + WRAPPER
        article_build_result_text += header.replace('h1', 'h2') + WRAPPER

        main_category = self._tags[0]
        main_category_en = _PartsBuilder.get_tag_en(main_category)
        href_value__tag__map_list = []
        href_value__tag__map_list.append({'href_value':BLOG_ROOT_URL, 'tag':PANKUZU_HOME_DISPLAY_TEXT})
        href_value__tag__map_list.append({'href_value':'{}{}/{}/'.format(BLOG_ROOT_URL, OUTPUT_SEARCH_DIRECTORY_NAME, main_category_en), 'tag':main_category})
        href_value__tag__map_list.append({'href_value':None, 'tag':'本記事'})
        article_build_result_text += _PartsBuilder.write_pankuzu_list_html(href_value__tag__map_list)
        image_link = '../../image/index/{}'.format(self._image_name)

        article_build_result_text += '<main id="main" itemprop="mainContentOfPage" itemscope itemtype="http://schema.org/Blog" role="main">' + WRAPPER
        article_build_result_text += '<article itemscope itemtype="http://schema.org/BlogPosting" itemprop="blogPost">' + WRAPPER
        article_build_result_text += '<h1 itemprop="name headline">' + WRAPPER
        article_build_result_text += '    {}'.format(self._title.replace('】', '】<br>').replace('（', '<br><span class="title-weak">（').replace('）', '）</span>').replace(' - ', '<br>')) + WRAPPER
        article_build_result_text += '</h1>' + WRAPPER
        article_build_result_text += '<div id="article-header">' + WRAPPER
        article_build_result_text += '    <div id="article-header-image">' + WRAPPER
        article_build_result_text += f'        <img class="article-image" src="{image_link}" alt="記事イメージ"/>' + WRAPPER
        article_build_result_text += '    </div>' + WRAPPER
        article_build_result_text += '    <p>' + WRAPPER
        article_build_result_text += f'        <time datetime="{self._post_date.strftime("%Y-%m-%d")}" itemprop="datePublished">{self._post_date.year}年{self._post_date.month}月{self._post_date.day}日</time>' + WRAPPER
        if self._update_date is not None:
            article_build_result_text += f'        <br>（最終更新日：<time datetime="{self._update_date.strftime("%Y-%m-%d")}" itemprop="dateModified">{self._update_date.year}年{self._update_date.month}月{self._update_date.day}日<time>）' + WRAPPER
        article_build_result_text += '    </p>' + WRAPPER
        article_build_result_text += '    <ul class="tags" itemprop="keywords">' + WRAPPER

        for tag in self._tags:
            article_build_result_text += _PartsBuilder.write_tag_link(tag=tag) + WRAPPER

        article_build_result_text += '    </ul>' + WRAPPER
        article_build_result_text += '</div>' + WRAPPER

        #article main
        text = '<div id="article-main" itemprop="articleBody">' + WRAPPER
        lines = self._contents.split('\n')

        code_now = False
        TABLE_OF_CONTENTS_PLACEHOLDER = 'title-placeholder-ds03445v5t3143f3965634'
        table_of_contents = []
        current_title_of_content = None

        code_now = False
        ad_added_count = 0
        table_of_contents_witten = False
        subtitle_counter = 1
        has_syntax_highlight = False
        need_to_write_purpose = True

        for i in range(len(lines)):
            line = lines[i]

            if line.startswith(MARKDOWN_CODE_FLAG):
                has_syntax_highlight = True
                if code_now:
                    text += WRAPPER + '</code></pre>' + WRAPPER
                else:
                    language = line.replace(MARKDOWN_CODE_FLAG, '')
                    text += '<pre>'
                    if language != '':
                        text += f'<span class="language">{language}</span>'
                    text += '<code>'
                code_now = not code_now
            elif line.startswith('>'):
                if i == 0 or not lines[i - 1].startswith('>'):
                    text += '<div class="quote">'

                if len(line) >= 2:
                    text += line[1:] + '<br>'
                else:
                    text += '<br>'

                if len(lines) == i or not lines[i + 1].startswith('>'):
                    text += '</div>'

            elif code_now:
                text += line.replace('<', '&lt;').replace('>', '&gt;')
            elif line.startswith('a!'):
                sp = line.split('!')
                link_href = sp[2]
                link_title = sp[3]
                link_description = sp[4]
                link_img = '<img src="../../image/{}/{}" alt="{}" width="100" height="100"/>'.format(os.path.basename(self._article_file_path).replace('.html', ''), sp[1], link_title)

                text += '<div class="link-box">' + WRAPPER
                text += '    <div class="link-img-column">' + WRAPPER
                text += f'        {link_img}' + WRAPPER
                text += '    </div>' + WRAPPER
                text += '    <div class="link-text-column">' + WRAPPER
                text += f'       <span class="related-link-prefix">関連リンク：</span><a href="{link_href}" target="_blank" rel="noopener noreferrer"><span class="link-title">{link_title}</span></a>' + WRAPPER
                text += '        <div class="link-description">' + WRAPPER
                text += f'            <span>{link_description}</span>' + WRAPPER
                text += '        </div>' + WRAPPER
                text += '    </div>' + WRAPPER
                text += '</div>' + WRAPPER
            elif line.startswith('!Quote!'):
                text += '<p class="quote-source paragraph-on-article">'
                text += "    引用元：" + line.replace('!Quote!', '')
                text += '</p>'
            elif line == '':
                continue
            elif line.startswith('#'):
                if line.startswith('#####'):
                    tag = 'h6'
                    text += f'<{tag}>' + WRAPPER
                    text += f'    {line[3:]}' + WRAPPER
                    text += f'</{tag}>' + WRAPPER
                if line.startswith('####'):
                    tag = 'h5'
                    text += f'<{tag}>' + WRAPPER
                    text += f'    {line[3:]}' + WRAPPER
                    text += f'</{tag}>' + WRAPPER
                if line.startswith('###'):
                    tag = 'h4'
                    text += f'<{tag}>' + WRAPPER
                    text += f'    {line[3:]}' + WRAPPER
                    text += f'</{tag}>' + WRAPPER
                elif line.startswith('##'):
                    class_attr_value="markered-title"
                    if need_to_write_purpose:
                        text += f'<h2 class="{class_attr_value}"><span>{line[2:]}</span></{tag}>' + WRAPPER
                    else:
                        tag_id = f'article-semi-subtitle-{len(table_of_contents)}-{len(current_title_of_content._children)}'
                        current_title_of_content._children.append(_TableOfContent(id=tag_id, display=line[2:]))
                        tag = 'h3'
                        text += f'<h3 id="{tag_id}" class="{class_attr_value}"><span>{line[2:]}</span></{tag}>' + WRAPPER
                else:
                    if current_title_of_content is not None:
                        table_of_contents.append(current_title_of_content)
                    tag_id = f'article-subtitle-{len(table_of_contents)}'
                    current_title_of_content = _TableOfContent(id=tag_id, display=line[1:])
                    need_to_write_purpose = False
                    tag = f'h2'
                    attibute = f' id="{tag_id}" class="section-title"'
                    subtitle_counter += 1
                    if not table_of_contents_witten:
                        table_of_contents_witten = True
                        text += TABLE_OF_CONTENTS_PLACEHOLDER + WRAPPER
                    elif (len(table_of_contents) >= 2 or line.startswith('#結び')) and ad_added_count == 0:
                        ad_added_count += 1
                        text += _google_ad_inline
                    text += f'<{tag}{attibute}>{line[1:]}</{tag}>' + WRAPPER
            elif line.startswith('-'):
                written = False
                if i == 0 or not lines[i - 1].startswith('-'):
                    text += '<div class="enumeration">' + WRAPPER
                    if line[1] == '-':
                        text += f'<span class="enumeration-title">{line[2:]}</span>' + WRAPPER
                        text += '<ul>' + WRAPPER
                        written = True
                    else:
                        text += '<ul>' + WRAPPER
                if not written:
                    text += '    <li>{}</li>'.format(line[1:])
                if i == len(lines) - 1 or not lines[i + 1].startswith('-'):
                    text += '</ul></div>' + WRAPPER
            elif line.startswith('!'):
                img_info = line[1:].split('!')
                if len(img_info) <= 1:
                    print(f'error: {self._article_file_path}, {line}')
                    raise Exception()
                text += '<figure>' + WRAPPER
                if img_info[1] != '':
                    text += f'    <figcaption>{img_info[1]}</figcaption>' + WRAPPER
                if len(img_info) >= 3:
                    alt = img_info[2]
                elif img_info[1] != '':
                    alt = img_info[1].split('。')[0]
                else:
                    alt = img_info[0].split('.')[0]
                text += '    <img src="../../image/{}/{}" alt="{}"/>'.format(os.path.basename(self._article_file_path).replace('.html', ''), img_info[0], alt) + WRAPPER
                text += '</figure>' + WRAPPER
            elif line.startswith('$'):
                candidate = list(filter(lambda x: os.path.basename(x._article_file_path).replace('.html', '') == line[1:], article_list_wrapper._articles))
                if len(candidate) == 0:
                    raise Exception(f'the related article name "{line[1:]}" is not found.')
                article = candidate[0]
                text += '<div class="related-article">' + WRAPPER
                text += f'    <span>関連記事：<a href="{article._absolute_url}">{article._title}</a></span>' + WRAPPER
                text += '</div>' + WRAPPER
            else:
                text += '<p class="paragraph-on-article">' + WRAPPER
                text += '    ' + line + WRAPPER
                text += '</p>' + WRAPPER
            text += WRAPPER

        table_of_contents.append(current_title_of_content)
        table_of_contents_text = ''
        table_of_contents_text += '<div id="table-of-contents">' + WRAPPER
        table_of_contents_text += '    <p>' + WRAPPER
        table_of_contents_text += '        ◇目次' + WRAPPER
        table_of_contents_text += '    </p>' + WRAPPER
        table_of_contents_text += '    <ol>' + WRAPPER
        for i in range(len(table_of_contents)):
            table_of_contents_text += table_of_contents[i].write_table_of_contents_part()
        table_of_contents_text += '    </ol>' + WRAPPER
        table_of_contents_text += '</div>' + WRAPPER
        text = text.replace(TABLE_OF_CONTENTS_PLACEHOLDER, table_of_contents_text)

        if main_category in PUSH_CONTACT_TAGS:
            text += '<h2 class="section-title">記事筆者へのお問い合わせ</h2>' + WRAPPER
            text += '<p class="paragraph-on-article">' + WRAPPER
            text += '    当社では、IT活用をはじめ、業務効率化やM&amp;A、管理会計など幅広い分野でコンサルティング事業・IT開発事業を行っております。' + WRAPPER
            text += '</p>' + WRAPPER
            text += '<p class="paragraph-on-article">' + WRAPPER
            text += '    この記事をご覧になり、もし相談してみたい点などがあれば、ぜひ問い合わせフォームまでご連絡ください。' + WRAPPER
            text += '</p>' + WRAPPER
            text += '<p class="paragraph-on-article">' + WRAPPER
            text += '    皆様のご投稿をお待ちしております。' + WRAPPER
            text += '</p>' + WRAPPER
            text += '<a href="https://it.sakai-sc.co.jp/contact/" target="_blank">' + WRAPPER
            text += '    <p class="button-on-article">' + WRAPPER
            text += '        記事筆者へ問い合わせする' + WRAPPER
            text += '    </p>' + WRAPPER
            text += '</a>' + WRAPPER
            text += '<span class="contact-button-description">※ご相談は無料でお受けいたします。</span>' + WRAPPER
        text += '</div>' + WRAPPER


        #article_build_result_text += text.replace('<strong>', '<span class="strong">').replace('</strong>', '</span>')
        article_build_result_text += text

        article_title_quote = urllib.parse.quote(self._title)

        article_build_result_text += '<div id="share-on-sns">' + WRAPPER
        article_build_result_text += '    <h2>SNSでシェア</h2>' + WRAPPER
        article_build_result_text += '    <ul id="sns_button">' + WRAPPER
        article_build_result_text += '        <li>' + WRAPPER
        article_build_result_text += f'            <a href="http://www.facebook.com/sharer.php?u={self._absolute_url}&t={article_title_quote}" target="_blank" rel="noopener noreferrer">' + WRAPPER
        article_build_result_text += '                <div class="link-facebook">' + WRAPPER
        article_build_result_text += '                    <img class="sns-icon" src="{}image/sns/f_logo_RGB-White_72.png" alt="facebook logo">'.format(BLOG_ROOT_URL) + WRAPPER
        article_build_result_text += '                    <span>facebook</span>' + WRAPPER
        article_build_result_text += '                </div>' + WRAPPER
        article_build_result_text += '            </a>' + WRAPPER
        article_build_result_text += '        </li>' + WRAPPER
        article_build_result_text += '        <li>' + WRAPPER
        article_build_result_text += f'            <a href="http://twitter.com/share?text={article_title_quote}&url={self._absolute_url}" target="_blank" rel="noopener noreferrer">' + WRAPPER
        article_build_result_text += '                <div class="link-twitter">' + WRAPPER
        article_build_result_text += '                    <img class="sns-icon" src="{}image/sns/2021 Twitter logo - white.png" alt="twitter logo">'.format(BLOG_ROOT_URL) + WRAPPER
        article_build_result_text += '                    <span>Twitter</span>' + WRAPPER
        article_build_result_text += '                </div>' + WRAPPER
        article_build_result_text += '            </a>' + WRAPPER
        article_build_result_text += '        </li>' + WRAPPER
        article_build_result_text += '        <li>' + WRAPPER
        article_build_result_text += f'            <a href="http://b.hatena.ne.jp/add?mode=confirm&url={self._absolute_url}&title={article_title_quote}" target="_blank" rel="noopener noreferrer">' + WRAPPER
        article_build_result_text += '                <div class="link-hatebu">' + WRAPPER
        article_build_result_text += '                    <img class="sns-icon" src="{}image/sns/b_hatena.png" alt="hatebu logo">'.format(BLOG_ROOT_URL) + WRAPPER
        article_build_result_text += '                    <span>hatebu</span>' + WRAPPER
        article_build_result_text += '                </div>' + WRAPPER
        article_build_result_text += '            </a>' + WRAPPER
        article_build_result_text += '        </li>' + WRAPPER
        article_build_result_text += '        <li>' + WRAPPER
        article_build_result_text += f'            <a href="http://line.naver.jp/R/msg/text/?{article_title_quote}%0D%0A{self._absolute_url}" target="_blank" rel="noopener noreferrer">' + WRAPPER
        article_build_result_text += '                <div class="link-line">' + WRAPPER
        article_build_result_text += '                    <img class="sns-icon" src="{}image/sns/LINE_Brand_icon.png" alt="line logo">'.format(BLOG_ROOT_URL) + WRAPPER
        article_build_result_text += '                    <span>LINE</span>' + WRAPPER
        article_build_result_text += '                </div>' + WRAPPER
        article_build_result_text += '            </a>' + WRAPPER
        article_build_result_text += '        </li>' + WRAPPER
        article_build_result_text += '        <li>' + WRAPPER
        article_build_result_text += f'            <a href="http://getpocket.com/edit?url={self._absolute_url}&title={article_title_quote}" target="_blank" rel="noopener noreferrer">' + WRAPPER
        article_build_result_text += '                <div class="link-pocket">' + WRAPPER
        article_build_result_text += '                    <img class="sns-icon" src="{}image/sns/pocket.png" alt="pocket logo">'.format(BLOG_ROOT_URL) + WRAPPER
        article_build_result_text += '                    <span>Read Later</span>' + WRAPPER
        article_build_result_text += '                </div>' + WRAPPER
        article_build_result_text += '            </a>' + WRAPPER
        article_build_result_text += '        </li>' + WRAPPER
        article_build_result_text += '    </ul>' + WRAPPER
        article_build_result_text += '</div>' + WRAPPER

        article_build_result_text += f'<a href="https://www.sakai-sc.co.jp/lp/it/" target="_blank" rel="noopener noreferrer"><img src="{BLOG_ROOT_URL}image/lp-banner.webp" alt="IT活用経営を実現する - 堺財経電算合同会社" style="width: 100%; margin: 10px 0 10px 0;"></a>' + WRAPPER

        if ad_added_count <= 1:
            article_build_result_text += _google_ad_inline

        article_build_result_text += '</article>' + WRAPPER

        article_build_result_text += _PartsBuilder.get_aside_html(article_list_wrapper, build_root_path, articles_with_same_category, category_name, main_category, self) + WRAPPER

        article_build_result_text += '</main>' + WRAPPER
        article_build_result_text += footer + WRAPPER
        article_build_result_text += _PartsBuilder.body_end_scripts(has_syntax_highlight=has_syntax_highlight)
        article_build_result_text += '</body>' + WRAPPER
        article_build_result_text += '</html>' + WRAPPER
        output_path = "{}/{}/{}".format(output_directory_path, OUTPUT_ARTICLE_DIRECTORY_NAME, _PartsBuilder.get_tag_en(self._tags[0]))
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        with open("{}/{}".format(output_path, os.path.basename(self._article_file_path)), mode="w", encoding='UTF-8') as f:
            f.write(article_build_result_text)

    def get_og_image_save_relative_path(self):
        return f'{OUTPUT_OG_IMAGE_DIRECTORY_NAME}/{os.path.basename(self._article_file_path).replace(".html", "")}.png'

    def generate_og_image(self):
        img = cv2.imread(OG_IMAGE_BASE)
        LINE_MAX_CHARS = 38
        article_title_fulltext_base = self._title.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('$#39;', '\'')

        msg_lines = []
        msg_line_builder = ''
        for i in range(len(article_title_fulltext_base)):
            char = article_title_fulltext_base[i]
            if len(article_title_fulltext_base) == i + 1:
                next_char = None
            else:
                next_char = article_title_fulltext_base[i + 1]

            msg_line_builder += char

            if char == '】' or ((char == '）' or char == '-' or char == '、') and len(msg_line_builder) > 10):
                msg_lines.append(msg_line_builder)
                if char == '】':
                    msg_lines.append('')
                msg_line_builder = ''
            elif len(msg_line_builder) >= LINE_MAX_CHARS / 2 and next_char not in ('】', '。', '？', '?', '、'):
                msg_lines.append(msg_line_builder)
                msg_line_builder = ''

        if msg_line_builder != '':
            msg_lines.append(msg_line_builder)

        img = Image.fromarray(img)
        draw = ImageDraw.Draw(img)

        FONT_SIZE_OF_TITLE = 58
        FONT_SIZE_OF_MAIN = 50
        
        if '【' in article_title_fulltext_base and '】' in article_title_fulltext_base:
            font_size = FONT_SIZE_OF_TITLE
        else:
            font_size = FONT_SIZE_OF_MAIN

        for i in range(len(msg_lines)):
            msg_line = msg_lines[i]
            
            if i == 0:
                offset_to_y = 100 
            elif i == 1 and '】' in msg_line:
                offset_to_y += 82
            else:
                offset_to_y += 66   
            font = ImageFont.truetype(OG_IMAGE_FONT_FILE, font_size)
            draw.text((80, offset_to_y), msg_line, font=font, fill=(64, 64, 64, 0))

            if font_size == FONT_SIZE_OF_TITLE and '】' in msg_line:
                font_size = FONT_SIZE_OF_MAIN

        img = np.array(img)

        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    def get_article_relative_url(cls, relative_path_prefix):
        '''
        relative_path_prefix = '' '../' or '../../'
        '''
        absolute_url = cls.get_article_absolute_url()
        return absolute_url.replace(BLOG_ROOT_URL, relative_path_prefix)

    def get_article_absolute_url(self):
        category_en = _PartsBuilder.get_tag_en(self._tags[0])
        return '{}{}/{}/{}'.format(BLOG_ROOT_URL, OUTPUT_ARTICLE_DIRECTORY_NAME, category_en, os.path.basename(self._article_file_path))

class _PartsBuilder:
    @classmethod
    def build_head(cls, build_root_path, head_infomation_map, page_title, page_category, article=None, tag=None, list_page_index = None, noindex = False):
        now = datetime.datetime.now()
        deploy_timestamp = f'deploy-id={now.year + now.month + now.day + now.hour + now.minute + now.second}'
        relateve_prefix = _Relateve_Prefix.get(page_category=page_category)

        if page_category == _PageCategory.INDEX:
            page_url = BLOG_ROOT_URL
        elif page_category == _PageCategory.SEARCH:
            page_url = '{}{}/{}/'.format(BLOG_ROOT_URL, OUTPUT_SEARCH_DIRECTORY_NAME, cls.get_tag_en(tag))
        elif page_category == _PageCategory.ARTICLE_LIST:
            page_url = '{}{}/'.format(BLOG_ROOT_URL, OUTPUT_SEARCH_DIRECTORY_NAME)
        elif page_category == _PageCategory.ARTICLE_LIST_WITH_INDEX:
            page_url = '{}{}/{}.html'.format(BLOG_ROOT_URL, OUTPUT_ARTICLE_DIRECTORY_NAME, list_page_index)
        elif page_category == _PageCategory.ARTICLE:
            page_url = article._absolute_url

        if article is not None:
            description = article._description.replace('"', '\'')
        else:
            description = head_infomation_map['blog_description'].replace('"', '\'')

        text = '<!DOCTYPE html>' + WRAPPER
        text += '<!--' + WRAPPER
        text += '    ソースコードにご関心をいただき、誠にありがとうございます！' + WRAPPER
        text += '    当ブログでは、ワードプレスなどのCMSを使わず、静的ファイルをスクラッチビルドしています。' + WRAPPER
        text += WRAPPER
        text += '    Githubにビルド用コードを公開しています。ご参考いただければ幸いです。' + WRAPPER
        text += '    https://github.com/Sakai3578/b-builder' + WRAPPER
        text += '-->' + WRAPPER
        text += '<html lang="ja">' + WRAPPER
        if article is None:
            text += '<head prefix="og: http://ogp.me/ns# fb: http://ogp.me/ns/fb# article: http://ogp.me/ns/article#" itemscope itemtype="http://schema.org/Organization">' + WRAPPER
        else:
            text += '<head prefix="og: http://ogp.me/ns# fb: http://ogp.me/ns/fb# website: http://ogp.me/ns/website#" itemscope itemtype="http://schema.org/Organization">' + WRAPPER
        text += '    <meta charset="UTF-8">' + WRAPPER
        text += '    <meta http-equiv="X-UA-Compatible" content="IE=edge">' + WRAPPER

        text += '    <meta property="og:url" content="{}" />'.format(page_url) + WRAPPER
        text += '    <meta property="og:title" content="{}" />'.format(page_title) + WRAPPER
        text += '    <meta property="og:description" content="{}" />'.format(description) + WRAPPER
        text += '    <meta property="og:site_name" content="{}" />'.format(head_infomation_map['blog_title']) + WRAPPER
        if article is None:
            text += '    <meta property="og:type" content="blog" />' + WRAPPER
        else:
            text += '    <meta property="og:type" content="article" />' + WRAPPER
        if article is None:
            text += '    <meta property="og:image" content="{}" />'.format(head_infomation_map['og_image']) + WRAPPER
        else:
            text += '    <meta property="og:image" content="{}" />'.format(f'{BLOG_ROOT_URL}{article.get_og_image_save_relative_path()}') + WRAPPER            
        text += '    <meta name="twitter:card" content="summary_large_image"/>' + WRAPPER
        text += '    <meta name="twitter:site" content="{}"/>'.format(head_infomation_map['twitter_site']) + WRAPPER
        text += '    <meta name="twitter:creator" content="{}"/>'.format(head_infomation_map['twitter_creator']) + WRAPPER
        text += '    <meta name="twitter:title" content="{}"/>'.format(page_title) + WRAPPER
        text += '    <meta name="twitter:description" content="{}"/>'.format(description) + WRAPPER
        text += '    <meta itemprop="name" content="堺財経電算合同会社">' + WRAPPER
        text += '    <meta itemprop="url" content="https://www.sakai-sc.co.jp/">' + WRAPPER
        text += '    <meta itemprop="about" content="堺財経電算合同会社は、「ITエンジニアリング」と「経営コンサルティング」の2つの知見を併せ持つプロフェッショナルとしてお客様をサポートいたします。">' + WRAPPER
        text += '    <link rel="canonical" href="{}" />'.format(page_url) + WRAPPER
        text += '    <link rel="icon" href="{}image/sakai-it.ico">'.format(relateve_prefix) + WRAPPER
        text += '    <link rel="apple-touch-icon" href="{}image/sakai-it.ico" sizes="180x180">'.format(relateve_prefix) + WRAPPER
        text += '    <meta name="viewport" content="width=device-width, initial-scale=1">' + WRAPPER
        text += '    <meta name="description" content="{}">'.format(description) + WRAPPER
        if noindex:
            text += '    <meta name="robots" content="noindex">' + WRAPPER
        else:
            text += '    <meta name="robots" content="max-snippet:-1, max-image-preview:large, max-video-preview:-1" />' + WRAPPER
        text += '    <title>{}</title>'.format(page_title) + WRAPPER
        text += '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3705637168814299"' + WRAPPER
        text += '    crossorigin="anonymous"></script>' + WRAPPER
        text += '    <link rel="stylesheet" type="text/css" href="{}style/hf.css?{}" />'.format(relateve_prefix, deploy_timestamp) + WRAPPER
        text += '    <link rel="stylesheet" type="text/css" href="{}style/aside.css?{}" />'.format(relateve_prefix, deploy_timestamp) + WRAPPER
        if page_category == _PageCategory.INDEX:
            text += '    <link rel="stylesheet" type="text/css" href="{}style/index.css?{}" />'.format(relateve_prefix, deploy_timestamp) + WRAPPER
        elif page_category == _PageCategory.SEARCH:
            text += '    <link rel="stylesheet" type="text/css" href="{}style/index.css?{}" />'.format(relateve_prefix, deploy_timestamp) + WRAPPER
        elif page_category == _PageCategory.ARTICLE_LIST:
            text += '    <link rel="stylesheet" type="text/css" href="{}style/index.css?{}" />'.format(relateve_prefix, deploy_timestamp) + WRAPPER
        elif page_category == _PageCategory.ARTICLE_LIST_WITH_INDEX:
            text += '    <link rel="stylesheet" type="text/css" href="{}style/index.css?{}" />'.format(relateve_prefix, deploy_timestamp) + WRAPPER
        elif page_category == _PageCategory.ARTICLE:
            now = datetime.datetime.now()
            text += '    <link rel="stylesheet" type="text/css" href="{}style/article.css?{}" />'.format(relateve_prefix, deploy_timestamp) + WRAPPER

        text += '    <script type="application/ld+json">' + WRAPPER
        text += '        {"@context":"https:\/\/schema.org","@graph":[{"@type":"WebSite","@id":"https:\/\/it.sakai-sc.co.jp\/#website","url":"https:\/\/it.sakai-sc.co.jp\/","name":"sakai-IT","inLanguage":"ja","publisher":{"@id":"https:\/\/it.sakai-sc.co.jp\/#person"}},{"@type":"Person","@id":"https:\/\/it.sakai-sc.co.jp\/#person","name":"堺　康行","image":{"@type":"ImageObject","@id":"https:\/\/it.sakai-sc.co.jp\/#personImage","url":"https://it.sakai-sc.co.jp/image/sakai.webp","width":96,"height":96,"caption":"堺　康行"}},{"@type":"BreadcrumbList","@id":"https:\/\/it.sakai-sc.co.jp\/#breadcrumblist","itemListElement":[{"@type":"ListItem","@id":"https:\/\/it.sakai-sc.co.jp\/#listItem","position":1,"item":{"@type":"WebPage","@id":"https:\/\/it.sakai-sc.co.jp\/","name":"\u30db\u30fc\u30e0","description":"sakai-IT\u306f\u3001IT\u6d3b\u7528\u7d4c\u55b6\u3084\u30d7\u30ed\u30b0\u30e9\u30df\u30f3\u30b0\u306a\u3069\u306e\u30c8\u30d4\u30c3\u30af\u3092\u63b2\u8f09\u3059\u308b\u30d6\u30ed\u30b0\u30e1\u30c7\u30a3\u30a2\u3067\u3059\u3002\u6700\u524d\u7dda\u3067\u6d3b\u52d5\u3059\u308b\u7d4c\u55b6\u30b3\u30f3\u30b5\u30eb\u30bf\u30f3\u30c8\u517c\u30a8\u30f3\u30b8\u30cb\u30a2\u304c\u8a18\u4e8b\u3092\u63b2\u8f09\u3057\u307e\u3059\u3002","url":"https:\/\/it.sakai-sc.co.jp\/"}}]},{"@type":"CollectionPage","@id":"https:\/\/it.sakai-sc.co.jp\/#collectionpage","url":"https:\/\/it.sakai-sc.co.jp\/","name":"sakai-IT","description":"sakai-IT\u306f\u3001IT\u6d3b\u7528\u7d4c\u55b6\u3084\u30d7\u30ed\u30b0\u30e9\u30df\u30f3\u30b0\u306a\u3069\u306e\u30c8\u30d4\u30c3\u30af\u3092\u63b2\u8f09\u3059\u308b\u30d6\u30ed\u30b0\u30e1\u30c7\u30a3\u30a2\u3067\u3059\u3002\u6700\u524d\u7dda\u3067\u6d3b\u52d5\u3059\u308b\u7d4c\u55b6\u30b3\u30f3\u30b5\u30eb\u30bf\u30f3\u30c8\u517c\u30a8\u30f3\u30b8\u30cb\u30a2\u304c\u8a18\u4e8b\u3092\u63b2\u8f09\u3057\u307e\u3059\u3002","inLanguage":"ja","isPartOf":{"@id":"https:\/\/www.sakai-sc.co.jp\/#website"},"breadcrumb":{"@id":"https:\/\/www.sakai-sc.co.jp\/#breadcrumblist"},"about":{"@id":"https:\/\/www.sakai-sc.co.jp\/#person"}}]}' + WRAPPER
        text += '    </script>' + WRAPPER

        with open(build_root_path + '/google_analytics/google_analytics.txt', 'r', encoding='UTF-8') as ga:
            text += ga.read()        
        text += '</head>' + WRAPPER
        return text

    @classmethod
    def build_index_or_search_html(cls, build_root_path, head_infomation_map, articles, header, aside, footer, display_title, page_category, breadcrumbs_href_value__tag__map_list, page_index = None, total_number_of_index_pages = None, display_range_text = None):
        relative_path_prefix = _Relateve_Prefix.get(page_category=page_category)
        tag = None
        if page_category == _PageCategory.ARTICLE or page_category == _PageCategory.SEARCH:
            tag = breadcrumbs_href_value__tag__map_list[len(breadcrumbs_href_value__tag__map_list) - 1]['tag']

        if page_category == _PageCategory.INDEX:
            page_title = "{} | {}".format(head_infomation_map['blog_title'], head_infomation_map['blog_subtitle'])
        elif page_category == _PageCategory.SEARCH:
            page_title = "{} を含む記事一覧 | {}".format(tag, head_infomation_map['blog_title'])
        elif page_category == _PageCategory.ARTICLE_LIST:
            page_title = "全記事一覧 | {}".format(head_infomation_map['blog_title'])
        elif page_category == _PageCategory.ARTICLE_LIST_WITH_INDEX:
            page_title = f'記事一覧 - {page_index}ページ/全{total_number_of_index_pages}ページ | {head_infomation_map["blog_title"]}'

        index_build_result_text = cls.build_head(build_root_path, head_infomation_map=head_infomation_map, page_title=page_title, page_category=page_category, tag=tag, list_page_index=page_index, noindex=len(articles)<=5)
        index_build_result_text += '<body>' + WRAPPER
        index_build_result_text += header + WRAPPER
        index_build_result_text += '<p id="site-descriptopn-display">' + WRAPPER
        index_build_result_text += f'    {head_infomation_map["blog_description"]}' + WRAPPER
        index_build_result_text += '</p>' + WRAPPER
        index_build_result_text += cls.write_pankuzu_list_html(breadcrumbs_href_value__tag__map_list) + WRAPPER
        index_build_result_text += '<main id="main" itemprop="mainContentOfPage" itemscope itemtype="http://schema.org/Blog">' + WRAPPER
        index_build_result_text += '    <div id="news-box">' + WRAPPER
        index_build_result_text += f'        <h2 class="column-title">◇{display_title}</h2>' + WRAPPER
        index_build_result_text += '        <div id="news">' + WRAPPER

        for article in articles:
            index_build_result_text += cls.get_index_article_block(article=article, relative_path_prefix=relative_path_prefix)
        index_build_result_text += '            </div>' + WRAPPER
        if page_category in (_PageCategory.INDEX, _PageCategory.ARTICLE_LIST_WITH_INDEX):
            index_build_result_text += f'            <p class="display-range-text">' + WRAPPER
            index_build_result_text += f'                {display_range_text}' + WRAPPER
            index_build_result_text += f'            </p>' + WRAPPER
            index_build_result_text += '            <ul id="page-index-list">' + WRAPPER
            for i in range(total_number_of_index_pages):
                if i == 0:
                    if page_index == 1:
                        index_build_result_text += f'                <li class="page-index page-index-without-link">ホーム</li>' + WRAPPER
                    else:
                        index_build_result_text += f'                <a href="{BLOG_ROOT_URL}"><li class="page-index page-index-link">ホーム</li></a>' + WRAPPER
                elif page_index == (i + 1):
                    index_build_result_text += f'                <li class="page-index page-index-without-link">{i + 1}</li>' + WRAPPER
                elif page_category == _PageCategory.INDEX:
                    index_build_result_text += f'                <a href="{OUTPUT_ARTICLE_DIRECTORY_NAME}/{i + 1}.html"><li class="page-index page-index-link">{i + 1}</li></a>' + WRAPPER
                else:
                    index_build_result_text += f'                <a href="{i + 1}.html"><li class="page-index page-index-link">{i + 1}</li></a>' + WRAPPER
        index_build_result_text += '            </ul>' + WRAPPER
        index_build_result_text += '        </div>' + WRAPPER
        index_build_result_text += '    </div>' + WRAPPER
        index_build_result_text += aside
        index_build_result_text += '</main>' + WRAPPER
        index_build_result_text += footer + WRAPPER
        index_build_result_text += cls.body_end_scripts(has_syntax_highlight=False)
        index_build_result_text += '</body>' + WRAPPER
        index_build_result_text += '</html>' + WRAPPER
        return index_build_result_text

    @classmethod
    def get_head_infomation_map(cls, build_root_path):
        with open(build_root_path + '/head-items.txt', 'r', encoding='UTF-8') as f:
            head_infomation_map_content = f.read().split('\n')
        result = {}
        for line in head_infomation_map_content:
            kv = line.split('\t')
            if len(kv) == 2:
                result[kv[0]] = kv[1]
        return result

    @classmethod
    def get_html_from_second_line_to_end(cls, file_full_path):
        """
        for excludion css link in for each files
        """
        with open(file_full_path, 'r', encoding='UTF-8') as f:
            target_contents_list = f.read().split('\n')[1:]
        return '\n'.join(target_contents_list)

    @classmethod
    def get_article_mata_infomation(cls, article_file_path):
        with open(article_file_path, 'r', encoding='UTF-8') as f:
            content = f.read().split('\n')
        result = {}
        for line in content:
            kv = line.split('\t')
            result[kv[0]] = kv[1]
        return result
    @classmethod
    def get_index_article_block(cls, article, relative_path_prefix):
        image_link = '{}image/index/{}'.format(BLOG_ROOT_URL, article._image_name)
        article_link = article.get_article_relative_url(relative_path_prefix)

        index_build_result_text = ''
        index_build_result_text += '        <div class="article-block">' + WRAPPER
        index_build_result_text += '            <div class="article-column">' + WRAPPER
        index_build_result_text += f'                <a href="{article_link}"><img class="article-image" src="{image_link}" alt="{article._meta_infomation_map["article_title"]}"/></a>' + WRAPPER
        index_build_result_text += '            </div>' + WRAPPER
        index_build_result_text += '            <div class="article-column">' + WRAPPER
        index_build_result_text += '                <h3>' + WRAPPER
        index_build_result_text += f'                    <a href="{article_link}">{article._title}</a>' + WRAPPER
        index_build_result_text += '                </h3>' + WRAPPER
        index_build_result_text += '                <p>' + WRAPPER
        index_build_result_text += '                    <time datetime="{}" itemprop="datePublished">投稿日：{}年{}月{}日</time>'.format(article._post_date.strftime("%Y-%m-%d"), article._post_date.year, article._post_date.month, article._post_date.day) + WRAPPER
        if article._update_date is not None:
            index_build_result_text += '        <br><time datetime="{}" itemprop="dateModified">最終更新日：{}年{}月{}日</time>'.format(article._update_date.strftime("%Y-%m-%d"), article._update_date.year, article._update_date.month, article._update_date.day) + WRAPPER
        index_build_result_text += '                </p>' + WRAPPER
        index_build_result_text += '                <ul class="tags">' + WRAPPER
        for tag in article._tags:
            index_build_result_text += cls.write_tag_link(tag)
        index_build_result_text += '                </ul>' + WRAPPER
        index_build_result_text += '            </div>' + WRAPPER
        index_build_result_text += '        </div>' + WRAPPER
        return index_build_result_text

    @classmethod
    def get_aside_article_block(cls, article):
        related_article_text = '        <div class="pickup-article-container">' + WRAPPER
        related_article_text += f'            <a href="{article._absolute_url}">' + WRAPPER
        related_article_text += f'                <img class="article-image" src="{BLOG_ROOT_URL}/image/index/{article._image_name}" alt="記事イメージ"/>' + WRAPPER
        related_article_text += '                <p class="aside-article-title">' + WRAPPER
        related_article_text += f'                    {article._title}' + WRAPPER
        related_article_text += '                </p>' + WRAPPER
        related_article_text += '            </a>' + WRAPPER
        related_article_text += '        </div>' + WRAPPER
        return related_article_text
        
    @classmethod
    def body_end_scripts(cls, has_syntax_highlight):
        text = ''
        if has_syntax_highlight:
            text += '    <script src="{}js/highlight.min.js"></script>'.format(BLOG_ROOT_URL) + WRAPPER
            text += '    <link rel="stylesheet" type="text/css" href="{}style/tomorrow-night-bright.min.css"/>'.format(BLOG_ROOT_URL) + WRAPPER
            text += '    <script type="text/javascript">' + WRAPPER
            text += '        hljs.initHighlightingOnLoad();' + WRAPPER
            text += '    </script>' + WRAPPER
        text += '    <script>' + WRAPPER
        text += '        (adsbygoogle = window.adsbygoogle || []).push({});' + WRAPPER
        text += '        (adsbygoogle = window.adsbygoogle || []).push({});' + WRAPPER
        text += '        (adsbygoogle = window.adsbygoogle || []).push({});' + WRAPPER
        text += '    </script>' + WRAPPER
        return text

    @classmethod
    def tag_display(cls, tag):
        return tag.replace('&', '&amp;')
    @classmethod
    def tag_escaping(cls, tag):
        return tag.replace('&', '-and-').replace('#', '-sharp-')
    @classmethod
    def get_tag_en(cls, tag):
        if tag in tag_ens:
            return tag_ens[tag]
        else:
            return tag.lower().replace(' ', '_')
    @classmethod
    def write_tag_link(cls, tag):
        tag_en = cls.get_tag_en(tag)
        tag_escaped = cls.tag_escaping(tag_en)
        tag_for_display = cls.tag_display(tag)
        link = '{}{}/{}/'.format(BLOG_ROOT_URL, OUTPUT_ARTICLE_DIRECTORY_NAME, tag_escaped)
        tag_link_text = '        <li class="tag">' + WRAPPER
        tag_link_text += '            <a href="{}" rel="tag">'.format(link) + WRAPPER
        tag_link_text += '                {}'.format(tag_for_display) + WRAPPER
        tag_link_text += '            </a>' + WRAPPER
        tag_link_text += '        </li>' + WRAPPER
        return tag_link_text
    @classmethod
    def write_pankuzu_list_html(cls, href_value__tag__map_list):
        position_no = 1
        pankuzu_html = ''

        pankuzu_link_item_exists = len(list(filter(lambda x: x['href_value'] is not None, href_value__tag__map_list))) > 0

        if pankuzu_link_item_exists:
            pankuzu_html += '<div id="breadcrumbList" itemscope itemtype="http://schema.org/BreadcrumbList">' + WRAPPER
        else:
            pankuzu_html += '<div id="breadcrumbList">' + WRAPPER

        for href_value__tag__map in href_value__tag__map_list:
            if 'href_value' in href_value__tag__map and href_value__tag__map['href_value'] is not None:
                pankuzu_html += '    <div class="breadcrumb" itemprop="itemListElement" itemscope itemtype="http://schema.org/ListItem">' + WRAPPER
                pankuzu_html += '        <a href="{}" itemprop="item">'.format(href_value__tag__map['href_value'])
                pankuzu_html += '<span itemprop="name">{}</span>'.format(href_value__tag__map['tag'])
                pankuzu_html += '</a>' + WRAPPER
                pankuzu_html += '        <meta itemprop="position" content="{}" />'.format(position_no) + WRAPPER
                position_no += 1
                pankuzu_html += '    </div>' + WRAPPER
            else:
                pankuzu_html += '    <div class="breadcrumb">' + WRAPPER
                pankuzu_html += '        <span>{}</span>'.format(href_value__tag__map['tag']) + WRAPPER
                pankuzu_html += '    </div>' + WRAPPER
        pankuzu_html += '</div>' + WRAPPER
        #pankuzu_html += '</div>' + WRAPPER
        return pankuzu_html
    @classmethod
    def remove_before_run(cls, build_root_path):
        targets = []
        targets += glob.glob(f'{build_root_path}/{OUTPUT_OUTPUT_DIRECTORY_NAME}/{OUTPUT_SEARCH_DIRECTORY_NAME}/*')
        targets += [f'{build_root_path}/{OUTPUT_OUTPUT_DIRECTORY_NAME}/index.html']
        targets += glob.glob(f'{build_root_path}/{OUTPUT_OUTPUT_DIRECTORY_NAME}/{OUTPUT_ARTICLE_DIRECTORY_NAME}/*')
        for target in targets:
            if os.path.exists(target):
                if os.path.isdir(target):
                    shutil.rmtree(target)
                else:
                    os.remove(target)
    @classmethod
    def get_aside_html(cls, article_list_wrapper, build_root_path, articles_with_same_category = None, category_name = None, main_category = None, current_article = None):
        text = '<aside role="complementary" itemscope itemtype="http://schema.org/WPSideBar">' + WRAPPER
        text += '    <div class="aside-container" id="about-this-website">' + WRAPPER
        text += '        <h2>このサイトについて</h2>' + WRAPPER
        text += '        <p class="aside-text-paragraph">' + WRAPPER
        text += '             <a href="https://www.sakai-sc.co.jp/" target="_blank" rel="noopener noreferrer">堺財経電算合同会社</a>が運営するブログメディアサイトです。業務の一環として、中小企業の経営×IT活用術やプログラミングの話題を中心に発信しています。' + WRAPPER
        text += '        </p>' + WRAPPER
        text += '        <p class="aside-text-paragraph">' + WRAPPER
        text += '             経営コンサルティング全般からシステム設計、コーディングまで最前線で何でもこなしている、代表者の堺が執筆しています。' + WRAPPER
        text += '        </p>' + WRAPPER
        text += '        <p class="aside-text-paragraph">' + WRAPPER
        text += '             是非ご一読のほどよろしくお願いします。' + WRAPPER
        text += '        </p>' + WRAPPER
        text += '    </div>' + WRAPPER
        text += cls.get_html_from_second_line_to_end(build_root_path + '/common_parts/author.html') + WRAPPER

        related_article_text = '<div class="aside-container">' + WRAPPER
        related_article_text += f'    <h2 class="pickup-articles-title">「{category_name}」カテゴリの関連記事</h2>' + WRAPPER
        related_article_count = 0
        if articles_with_same_category is not None:
            for article_with_same_category in articles_with_same_category:
                if current_article._title == article_with_same_category._title:
                    continue
                related_article_text += cls.get_aside_article_block(article_with_same_category) + WRAPPER
                #related_article_text += _PartsBuilder.get_index_article_block(article=article_with_same_categpty, relative_path_prefix='../../') + WRAPPER
                if related_article_count == 4:
                    break
                else:
                    related_article_count += 1
            if related_article_count > 0:
                text += related_article_text
                text += '<p class="other-articles-link-box">'
                text += f'    <a href="../{_PartsBuilder.tag_escaping(_PartsBuilder.get_tag_en(category_name))}/" class="other-articles-link">'
                text += f'        「{category_name}」カテゴリをもっと見る'
                text += '    </a>'
                text += '</p>'
                if category_name != main_category:
                    text += '<p>'
                    text += f'    <a href="../{_PartsBuilder.tag_escaping(_PartsBuilder.get_tag_en(main_category))}/" class="other-articles-link">'
                    text += f'        「{main_category}」カテゴリをもっと見る'
                    text += '    </a>'
                    text += '</p>'
                text += '</div>' + WRAPPER

        else:
            text += '    <div class="aside-container">' + WRAPPER
            text += '        <h2 class="pickup-articles-title">' + WRAPPER
            text += '            ピックアップ記事' + WRAPPER
            text += '        </h2>' + WRAPPER
            for pickup_article_name in _pickup_article_names:
                article = list(filter(lambda x: x._file_name.replace('.html', '') == pickup_article_name, article_list_wrapper._articles))[0]
                text += cls.get_aside_article_block(article) + WRAPPER
            text += '    </div>' + WRAPPER

        text += '    <div class="ad-container">'
        text += _google_ad_vertical
        text += '    </div>' + WRAPPER
        text += '    <div class="banner-container">' + WRAPPER
        text += _aside_banners + WRAPPER
        text += '    </div>'
        #amazon link writing
        # if tags is not None:
        #     for target_tag, link_html in _amazon_links.items():
        #         if target_tag in tags:
        #             text += '    <div class="aside-amazon">' + WRAPPER
        #             text += '    <p>' + WRAPPER
        #             text += '        このジャンルのオススメ書籍' + WRAPPER
        #             text += '    </p>' + WRAPPER
        #             text += link_html + WRAPPER
        #             text += '    </div>' + WRAPPER
        #             break
        text += '</aside>' + WRAPPER
        return text

    @classmethod
    def sitemap_builder(cls, article_list_wrapper):
        text = '<?xml version="1.0" encoding="UTF-8"?>' + WRAPPER
        text += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' + WRAPPER
        text += '<url>' + WRAPPER
        text += '   <loc>{}</loc>'.format(BLOG_ROOT_URL) + WRAPPER
        text += '   <priority>1.0</priority>' + WRAPPER
        text += '</url>' + WRAPPER
        text += '<url>' + WRAPPER
        text += '   <loc>{}{}/</loc>'.format(BLOG_ROOT_URL, OUTPUT_ARTICLE_DIRECTORY_NAME) + WRAPPER
        text += '   <priority>0.9</priority>' + WRAPPER
        text += '</url>' + WRAPPER
        total_number_of_index_pages = article_list_wrapper.get_total_number_of_index_pages()
        if total_number_of_index_pages >= 2:
            for i in range(1, total_number_of_index_pages):
                text += '<url>' + WRAPPER
                text += f'   <loc>{BLOG_ROOT_URL}{OUTPUT_ARTICLE_DIRECTORY_NAME}/{i + 1}.html</loc>' + WRAPPER
                text += '   <priority>0.9</priority>' + WRAPPER
                text += '</url>' + WRAPPER
        for article in article_list_wrapper._articles:
            article_url = article._absolute_url
            text += '<url>' + WRAPPER
            text += f'   <loc>{article_url}</loc>' + WRAPPER
            text += '   <priority>0.8</priority>' + WRAPPER
            if article._update_date is not None:
                text += '    <lastmod>{}</lastmod>'.format(article._update_date.strftime('%Y-%m-%d')) + WRAPPER
            else:
                text += '    <lastmod>{}</lastmod>'.format(article._post_date.strftime('%Y-%m-%d')) + WRAPPER
            text += '</url>' + WRAPPER
        for tag in article_list_wrapper.get_all_tags():
            if not tag in PICKUP_TAGS:
                continue
            text += '<url>' + WRAPPER
            text += f'   <loc>{BLOG_ROOT_URL}{OUTPUT_ARTICLE_DIRECTORY_NAME}/{_PartsBuilder.get_tag_en(tag)}/</loc>' + WRAPPER
            text += '   <priority>0.9</priority>' + WRAPPER
            text += '</url>' + WRAPPER
        
        text += '</urlset>' + WRAPPER
        return text

class _TableOfContent:
    def __init__(self, id, display):
        self._id = id
        self._display = display
        self._children = []
    def write_table_of_contents_part(self):
        text = ''
        text += '        <li>' + WRAPPER
        text += f'            <a href="#{self._id}">{self._display}</a>' + WRAPPER
        if len(self._children) > 0:
            text += '            <ul class="child-titles">' + WRAPPER
            for i in range(len(self._children)):
                child = self._children[i]
                text += '                <li>' + WRAPPER
                text += f'                    <a href="#{child._id}">{child._display}</a>' + WRAPPER
                text += '                </li>' + WRAPPER
            text += '            </ul>' + WRAPPER
        text += '        </li>' + WRAPPER
        return text

class _PageCategory:
    #トップページ
    INDEX = "index"
    #記事ページ
    ARTICLE = "article"
    #カテゴリ別リスト
    SEARCH = "search"
    #全記事一覧
    ARTICLE_LIST = "article-list"
    #2.html,3.html...
    ARTICLE_LIST_WITH_INDEX = "article-list-with-index" 

class _Relateve_Prefix:
    @classmethod
    def get(cls, page_category):
        if page_category == _PageCategory.INDEX:
            return ""
        if page_category == _PageCategory.ARTICLE:
            return "../../"
        if page_category == _PageCategory.SEARCH:
            return "../../"
        if page_category == _PageCategory.ARTICLE_LIST:
            return "../"
        if page_category == _PageCategory.ARTICLE_LIST_WITH_INDEX:
            return "../"

if __name__ == '__main__':
    main()
