import urllib.parse
import datetime
import glob
import os
import sys
import shutil

OUTPUT_OUTPUT_DIRECTORY_NAME = 'output'
OUTPUT_ARTICLE_DIRECTORY_NAME = 'article'
OUTPUT_SEARCH_DIRECTORY_NAME = 'article'
PANKUZU_HOME_DISPLAY_TEXT = 'ホーム'
PICKUP_TAGS = ['IT活用経営', 'プログラミング', 'AI開発']

RELATIVE_PREFIX_ARTICLE = '../../'
RELATIVE_PREFIX_SEARCH = '../../'
RELATIVE_PREFIX_INDEX = ''

MARKDOWN_CODE_FLAG = '```'

WRAPPER = '\n'
tag_ens = {}


def main():
    build(sys.argv[1])

def build(build_root_path):
    if build_root_path.endswith('/'):
        build_root_path = build_root_path[:len(build_root_path) - 1]
    _PartsBuilder.__remove_before_run(build_root_path)
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

    header = _PartsBuilder.__get_html_from_second_line_to_end(build_root_path + '/common_parts/header.html')
    aside_for_article = _PartsBuilder.__get_aside_html(build_root_path, is_index=False)
    aside_for_index = _PartsBuilder.__get_aside_html(build_root_path, is_index=True)
    footer = _PartsBuilder.__get_html_from_second_line_to_end(build_root_path + '/common_parts/footer.html')
    head_infomation_map = _PartsBuilder.__get_head_infomation_map(build_root_path)

    #article files
    article_list_wrapper = ArticleListWrapper(build_root_path=build_root_path)
    article_list_wrapper.save_article_files(head_infomation_map=head_infomation_map, header=header, aside=aside_for_article, footer=footer, output_directory_path=output_directory_path)

    #index file
    breadcrumbs_href_value__display_text__map_list = []
    breadcrumbs_href_value__display_text__map_list.append({'href_value':head_infomation_map['blog_root_url'], 'display_text':PANKUZU_HOME_DISPLAY_TEXT})
    _PartsBuilder.__save_index_file(build_root_path, head_infomation_map=head_infomation_map, articles=article_list_wrapper._articles, header=header, aside=aside_for_index, footer=footer, output_file_path=f'{build_root_path}/index.html', display_title='◇新着記事', relative_path_prefix=RELATIVE_PREFIX_INDEX, breadcrumbs_href_value__display_text__map_list=breadcrumbs_href_value__display_text__map_list)

    #build search files
    for tag, articles_with_the_tag in article_list_wrapper._tag_articles_map.items():
        breadcrumbs_href_value__display_text__map_list = []
        breadcrumbs_href_value__display_text__map_list.append({'href_value':head_infomation_map['blog_root_url'], 'display_text':PANKUZU_HOME_DISPLAY_TEXT})
        breadcrumbs_href_value__display_text__map_list.append({'href_value':None, 'display_text':tag})

        tag_en = _PartsBuilder.__get_tag_en(tag)
        save_dir = "{}/{}/{}".format(output_directory_path, OUTPUT_SEARCH_DIRECTORY_NAME, tag_en)
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)

        _PartsBuilder.__save_index_file(build_root_path, head_infomation_map=head_infomation_map, articles=articles_with_the_tag, header=header, aside=aside_for_index, footer=footer, output_file_path=f'{save_dir}/index.html', display_title=f'{tag} を含む記事の一覧', relative_path_prefix=RELATIVE_PREFIX_SEARCH, breadcrumbs_href_value__display_text__map_list=breadcrumbs_href_value__display_text__map_list)

    #build sitemap
    sitemap_content = _PartsBuilder.__sitemap_builder(head_infomation_map=head_infomation_map, articles=article_list_wrapper._articles)
    with open("{}/sitemap.xml".format(output_directory_path), mode="w", encoding='UTF-8') as f:
        f.write(sitemap_content)

    print(f'output terminated in {output_directory_path}.')


class ArticleListWrapper():
    def __init__(self, build_root_path):
        self._build_root_path = build_root_path
        article_html_files_path = glob.glob(build_root_path + "/articles/*.html")
        self._articles = [Article(article_file_path=x, meta_infomation_map=_PartsBuilder.__get_article_mata_infomation(x.replace('.html', '.txt'))) for x in article_html_files_path]
        self._articles.sort(key=lambda x: x._post_date, reverse=True)
        self._tag_articles_map = {}
    def save_article_files(self, head_infomation_map, header, aside, footer, output_directory_path):
        for article in self._articles:
            article.save_article_file(build_root_path=self._build_root_path, head_infomation_map=head_infomation_map, header=header, aside=aside, footer=footer, output_directory_path=output_directory_path, articles_with_same_categpty=self.get_article_objects_with_tag(article._tags[0]))
            for tag in article._tags:
                if tag in self._tag_articles_map:
                    self._tag_articles_map[tag].append(article)
                else:
                    self._tag_articles_map[tag] = [article]
    def get_latest_article_object(self):
        return self._articles[0]
    def get_article_objects_with_tag(self, tag):
        return list(filter(lambda x: tag in x._tags, self._articles))
        
class Article():
    def __init__(self, article_file_path, meta_infomation_map):
        self._article_file_path = article_file_path
        self._meta_infomation_map = meta_infomation_map
        post_date_parts = meta_infomation_map['post_date'].split('-')
        self._post_date = datetime.date(int(post_date_parts[0]), int(post_date_parts[1]), int(post_date_parts[2]))
        self._tags = meta_infomation_map["tags"].split(',')
        if 'update_date' in meta_infomation_map:
            update_date_text_split = meta_infomation_map['update_date'].split(' ')[0].split('-')
            update_time_text_split = meta_infomation_map['update_date'].split(' ')[1].split(':')
            update_date = datetime.datetime(int(update_date_text_split[0]), int(update_date_text_split[1]), int(update_date_text_split[2]), int(update_time_text_split[0]), int(update_time_text_split[1]), 0)
            if update_date.day != self._post_date.day or update_date.month != self._post_date.month or update_date.year != self._post_date.year:
                self._update_date = update_date
            else:
                self._update_date = None

    def save_article_file(self, build_root_path, head_infomation_map, header, aside, footer, output_directory_path, articles_with_same_categpty):
        article_build_result_text = _PartsBuilder.__build_head(build_root_path, head_infomation_map=head_infomation_map, meta_infomation_map=self._meta_infomation_map, article_file_path=self._article_file_path, article_title=self._meta_infomation_map['article_title']) + WRAPPER
        article_build_result_text += '<body>' + WRAPPER
        article_build_result_text += header.replace('h1', 'h2') + WRAPPER

        category = self._tags[0]
        category_en = _PartsBuilder.__get_tag_en(category)
        href_value__display_text__map_list = []
        href_value__display_text__map_list.append({'href_value':head_infomation_map['blog_root_url'], 'display_text':PANKUZU_HOME_DISPLAY_TEXT})
        href_value__display_text__map_list.append({'href_value':'{}{}/{}/'.format(head_infomation_map['blog_root_url'], OUTPUT_SEARCH_DIRECTORY_NAME, category_en), 'display_text':category})
        href_value__display_text__map_list.append({'href_value':None, 'display_text':'本記事'})
        article_build_result_text += _PartsBuilder.__write_pankuzu_list_html(href_value__display_text__map_list)

        article_build_result_text += '<main id="main" itemprop="mainContentOfPage" itemscope itemtype="http://schema.org/Blog">' + WRAPPER
        article_build_result_text += '<article itemscope itemtype="http://schema.org/BlogPosting" itemprop="blogPost">' + WRAPPER
        article_build_result_text += '<h1 itemprop="name headline">' + WRAPPER
        article_build_result_text += '    {}'.format(self._meta_infomation_map['article_title'].replace('】', '】<br>').replace(' - ', '<br class="wrap-if-wide-screen">').replace('、', '、<br class="wrap-if-wide-screen">')) + WRAPPER
        article_build_result_text += '</h1>' + WRAPPER
        article_build_result_text += '<div id="article-header">' + WRAPPER
        article_build_result_text += '    <p>' + WRAPPER
        article_build_result_text += '        {}年{}月{}日'.format(self._post_date.year, self._post_date.month, self._post_date.day) + WRAPPER
        article_build_result_text += '    </p>' + WRAPPER
        article_build_result_text += '    <ul class="tags" itemprop="keywords">' + WRAPPER
        article_build_result_text += '    </ul>' + WRAPPER
        article_build_result_text += '</div>' + WRAPPER

        #article main
        with open(self._article_file_path, 'r', encoding='UTF-8') as f:
            contents = f.read()
        text = '<div id="article-main" itemprop="articleBody">' + WRAPPER
        lines = contents.split('\n')

        titles = []
        code_now = False
        for line in lines:
            if line.startswith(MARKDOWN_CODE_FLAG):
                code_now = not code_now
            elif not code_now and line.startswith('#') and  line[1] != '#':
                titles.append(line[1:])

        code_now = False
        table_of_contents_witten = False
        subtitle_counter = 1

        for i in range(len(lines)):
            line = lines[i]
            if line.startswith(MARKDOWN_CODE_FLAG):
                if code_now:
                    text += WRAPPER + '</code></pre>' + WRAPPER
                else:
                    text += '<pre><code>'
                code_now = not code_now
            elif code_now:
                text += line.replace('<', '&lt;').replace('>', '&gt;')
            elif line == '':
                continue
            elif line.startswith('#'):
                if line.startswith('###'):
                    tag = 'h4'
                    text += f'<{tag}>' + WRAPPER
                    text += f'    {line[3:]}' + WRAPPER
                    text += f'</{tag}>' + WRAPPER
                elif line.startswith('##'):
                    tag = 'h2'
                    text += f'<{tag}>' + WRAPPER
                    text += f'    <span>{line[2:]}</span>' + WRAPPER
                    text += f'</{tag}>' + WRAPPER
                else:
                    tag = f'h3'
                    attibute = f' id="article-subtilte-{subtitle_counter}"'
                    subtitle_counter += 1
                    if not table_of_contents_witten:
                        table_of_contents_witten = True
                        text += '<div id="table-of-contents">'
                        text += '    <p>'
                        text += '        ◇目次'
                        text += '    </p>'
                        text += '    <ol>' + WRAPPER
                        for i in range(len(titles)):
                            text += '    <li>' + WRAPPER
                            text += f'        <a href="#article-subtilte-{i + 1}">{titles[i]}</a>' + WRAPPER
                            text += '    </li>' + WRAPPER
                        text += '    </ol>' + WRAPPER
                        text += '</div>' + WRAPPER
                    text += f'<{tag}{attibute}>{line[1:]}</{tag}>' + WRAPPER
            elif line.startswith('-'):
                if i == 0 or not lines[i - 1].startswith('-'):
                    text += '<div class="enumeration"><ul>' + WRAPPER
                text += '    <li>{}</li>'.format(line[1:])
                if i == len(lines) - 1 or not lines[i + 1].startswith('-'):
                    text += '</ul></div>' + WRAPPER
            elif line.startswith('!'):
                img_info = line[1:].split('!')
                text += '<figure>' + WRAPPER
                text += f'    <figcaption>＞{img_info[1]}</figcaption>' + WRAPPER
                text += '    <img src="../../image/{}/{}" alt="{}"/>'.format(os.path.basename(self._article_file_path).replace('.html', ''), img_info[0], img_info[0].split('.')[0]) + WRAPPER
                text += '</figure>' + WRAPPER
            else:
                text += '<p>' + WRAPPER
                text += '    ' + line + WRAPPER
                text += '</p>' + WRAPPER
            text += WRAPPER
        text += '</div>' + WRAPPER

        article_build_result_text += text.replace('<strong>', '<span class="strong">').replace('</strong>', '</span>')

        article_absolute_url = _PartsBuilder.__get_article_absolute_url(head_infomation_map, meta_infomation_map=self._meta_infomation_map, article_file_path=self._article_file_path)
        article_title_quote = urllib.parse.quote(self._meta_infomation_map["article_title"])

        article_build_result_text += '<div id="share_on_sns">' + WRAPPER
        article_build_result_text += '    <h2>SNSでシェア</h2>' + WRAPPER
        article_build_result_text += '    <ul id="sns_button">' + WRAPPER
        article_build_result_text += '        <li>' + WRAPPER
        article_build_result_text += f'            <a href="http://www.facebook.com/sharer.php?u={article_absolute_url}&t={article_title_quote}" target="_blank" rel="noopener noreferrer">' + WRAPPER
        article_build_result_text += '                <div class="link-facebook">' + WRAPPER
        article_build_result_text += '                    <img class="sns-icon" src="{}image/sns/f_logo_RGB-White_72.png" alt="facebook logo">'.format(RELATIVE_PREFIX_ARTICLE) + WRAPPER
        article_build_result_text += '                    <span>facebook</span>' + WRAPPER
        article_build_result_text += '                </div>' + WRAPPER
        article_build_result_text += '            </a>' + WRAPPER
        article_build_result_text += '        </li>' + WRAPPER
        article_build_result_text += '        <li>' + WRAPPER
        article_build_result_text += f'            <a href="http://twitter.com/share?text={article_title_quote}&url={article_absolute_url}" target="_blank" rel="noopener noreferrer">' + WRAPPER
        article_build_result_text += '                <div class="link-twitter">' + WRAPPER
        article_build_result_text += '                    <img class="sns-icon" src="{}image/sns/2021 Twitter logo - white.png" alt="twitter logo">'.format(RELATIVE_PREFIX_ARTICLE) + WRAPPER
        article_build_result_text += '                    <span>Twitter</span>' + WRAPPER
        article_build_result_text += '                </div>' + WRAPPER
        article_build_result_text += '            </a>' + WRAPPER
        article_build_result_text += '        </li>' + WRAPPER
        article_build_result_text += '        <li>' + WRAPPER
        article_build_result_text += f'            <a href="http://b.hatena.ne.jp/add?mode=confirm&url={article_absolute_url}&title={article_title_quote}" target="_blank" rel="noopener noreferrer">' + WRAPPER
        article_build_result_text += '                <div class="link-hatebu">' + WRAPPER
        article_build_result_text += '                    <img class="sns-icon" src="{}image/sns/b_hatena.png" alt="hatebu logo">'.format(RELATIVE_PREFIX_ARTICLE) + WRAPPER
        article_build_result_text += '                    <span>hatebu</span>' + WRAPPER
        article_build_result_text += '                </div>' + WRAPPER
        article_build_result_text += '            </a>' + WRAPPER
        article_build_result_text += '        </li>' + WRAPPER
        article_build_result_text += '        <li>' + WRAPPER
        article_build_result_text += f'            <a href="http://line.naver.jp/R/msg/text/?{article_title_quote}%0D%0A{article_absolute_url}" target="_blank" rel="noopener noreferrer">' + WRAPPER
        article_build_result_text += '                <div class="link-line">' + WRAPPER
        article_build_result_text += '                    <img class="sns-icon" src="{}image/sns/LINE_Brand_icon.png" alt="line logo">'.format(RELATIVE_PREFIX_ARTICLE) + WRAPPER
        article_build_result_text += '                    <span>LINE</span>' + WRAPPER
        article_build_result_text += '                </div>' + WRAPPER
        article_build_result_text += '            </a>' + WRAPPER
        article_build_result_text += '        </li>' + WRAPPER
        article_build_result_text += '        <li>' + WRAPPER
        article_build_result_text += f'            <a href="http://getpocket.com/edit?url={article_absolute_url}&title={article_title_quote}" target="_blank" rel="noopener noreferrer">' + WRAPPER
        article_build_result_text += '                <div class="link-pocket">' + WRAPPER
        article_build_result_text += '                    <img class="sns-icon" src="{}image/sns/pocket.png" alt="pocket logo">'.format(RELATIVE_PREFIX_ARTICLE) + WRAPPER
        article_build_result_text += '                    <span>Read Later</span>' + WRAPPER
        article_build_result_text += '                </div>' + WRAPPER
        article_build_result_text += '            </a>' + WRAPPER
        article_build_result_text += '        </li>' + WRAPPER
        article_build_result_text += '    </ul>' + WRAPPER
        article_build_result_text += '</div>' + WRAPPER

        current_category = self._meta_infomation_map['tags'].split(',')[0]
        related_article_text = '<div id="news">' + WRAPPER
        related_article_text += f'    <h2>{current_category} カテゴリーの最新記事</h2>' + WRAPPER
        related_article_count = 0
        for article_with_same_categpty in articles_with_same_categpty:
            related_article_text += _PartsBuilder.__get_index_article_block(article_file_path=article_with_same_categpty._article_file_path, head_infomation_map=head_infomation_map, meta_infomation_map=articles_with_same_categpty._meta_infomation_map, relative_path_prefix='../../') + WRAPPER
            if related_article_count == 4:
                break
            else:
                related_article_count += 1
        related_article_text += '</div>' + WRAPPER
        if related_article_count > 0:
            article_build_result_text += related_article_text

        article_build_result_text += '</article>' + WRAPPER
        article_build_result_text += aside + WRAPPER
        article_build_result_text += '</main>'
        article_build_result_text += footer + WRAPPER
        article_build_result_text += '</body>' + WRAPPER
        article_build_result_text += '</html>' + WRAPPER
        output_path = "{}/{}/{}".format(output_directory_path, OUTPUT_ARTICLE_DIRECTORY_NAME, _PartsBuilder.__get_tag_en(self.tags[0]))
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        with open("{}/{}".format(output_path, os.path.basename(self._article_file_path)), mode="w", encoding='UTF-8') as f:
            f.write(article_build_result_text)


class _PartsBuilder():
    @classmethod
    def __save_index_file(cls, build_root_path, head_infomation_map, articles, header, aside, footer, output_file_path, display_title, relative_path_prefix, breadcrumbs_href_value__display_text__map_list):
        index_build_result_text = cls.__build_head(build_root_path, head_infomation_map=head_infomation_map, is_index=True)
        index_build_result_text += '<body>' + WRAPPER
        index_build_result_text += header.replace('../', '') + WRAPPER
        index_build_result_text += cls.__write_pankuzu_list_html(breadcrumbs_href_value__display_text__map_list)
        index_build_result_text += '<main id="main" itemprop="mainContentOfPage" itemscope itemtype="http://schema.org/Blog">' + WRAPPER
        index_build_result_text += '    <div id="news-box">' + WRAPPER

        index_build_result_text += f'        <h2 class="column-title">{display_title}</h2>' + WRAPPER
        index_build_result_text += '        <div id="news">' + WRAPPER
        for article in articles:
            index_build_result_text += cls.__get_index_article_block(article._article_file_path, head_infomation_map=head_infomation_map, meta_infomation_map=article._meta_infomation_map, relative_path_prefix=relative_path_prefix)
        index_build_result_text += '        </div>' + WRAPPER
        index_build_result_text += '    </div>' + WRAPPER
        if relative_path_prefix == RELATIVE_PREFIX_INDEX:
            index_build_result_text += aside.replace('../', '')
        else:
            index_build_result_text += aside
        index_build_result_text += '</main>' + WRAPPER
        index_build_result_text += footer + WRAPPER
        index_build_result_text += '</body>' + WRAPPER
        index_build_result_text += '</html>' + WRAPPER
        with open(output_file_path, mode="w", encoding='UTF-8') as f:
            f.write(index_build_result_text)
        
    @classmethod
    def __get_head_infomation_map(cls, build_root_path):
        with open(build_root_path + '/head-items.txt', 'r', encoding='UTF-8') as f:
            head_infomation_map_content = f.read().split('\n')
        result = {}
        for line in head_infomation_map_content:
            kv = line.split('\t')
            if len(kv) == 2:
                result[kv[0]] = kv[1]
        return result

    @classmethod
    def __build_head(cls, build_root_path, head_infomation_map, meta_infomation_map=None, is_index=False, is_search_result=False, article_file_path=None, article_title=None, search_word=None):
        if is_index:
            relateive_prefix = ''
            page_title = "{} | {}".format(head_infomation_map['blog_title'], head_infomation_map['blog_subtitle'])
            page_url = head_infomation_map['blog_root_url']
        elif is_search_result:
            relateive_prefix = RELATIVE_PREFIX_SEARCH
            page_title = "{} を含む記事一覧 | {}".format(search_word, head_infomation_map['blog_title'])
            page_url = '{}{}/{}.html'.format(head_infomation_map['blog_root_url'], OUTPUT_SEARCH_DIRECTORY_NAME, search_word)
        else:
            relateive_prefix = RELATIVE_PREFIX_ARTICLE
            page_title = "{} | {}".format(article_title, head_infomation_map['blog_title'])
            page_url = cls.__get_article_absolute_url(head_infomation_map, meta_infomation_map=meta_infomation_map, article_file_path=article_file_path)

        text = '<!DOCTYPE html>' + WRAPPER
        text += '<html lang="ja" prefix="og: http://ogp.me/ns#">' + WRAPPER
        text += '<head>' + WRAPPER
        text += '    <meta charset="UTF-8">' + WRAPPER
        text += '    <meta http-equiv="X-UA-Compatible" content="IE=edge">' + WRAPPER

        if is_search_result:
            text += '    <meta name="robots" content="noindex">' + WRAPPER
        else:
            text += '    <meta property="og:url" content="{}" />'.format(page_url) + WRAPPER
            text += '    <meta property="og:title" content="{}" />'.format(page_title) + WRAPPER
            text += '    <meta property="og:description" content="{}" />'.format(head_infomation_map['blog_description']) + WRAPPER
            text += '    <meta property="og:site_name" content="{}" />'.format(head_infomation_map['blog_title']) + WRAPPER
            text += '    <meta property="og:type" content="website" />' + WRAPPER
            text += '    <meta property="og:image" content="{}" />'.format(head_infomation_map['og_image']) + WRAPPER
            text += '    <meta name="twitter:card" content="summary_large_image"/>' + WRAPPER
            text += '    <meta name="twitter:site" content="{}"/>'.format(head_infomation_map['twitter_site']) + WRAPPER
            text += '    <meta name="twitter:creator" content="{}"/>'.format(head_infomation_map['twitter_creator']) + WRAPPER
            text += '    <meta name="twitter:title" content="{}"/>'.format(page_title) + WRAPPER
            text += '    <meta name="twitter:description" content="{}"/>'.format(head_infomation_map['blog_description']) + WRAPPER
            text += '    <meta itemprop="name" content="堺財経電算合同会社">' + WRAPPER
            text += '    <meta itemprop="url" content="https://www.sakai-sc.co.jp/">' + WRAPPER
            text += '    <meta itemprop="about" content="堺財経電算合同会社は、「ITエンジニアリング」と「経営コンサルティング」の2つの知見を併せ持つプロフェッショナルとしてお客様をサポートいたします。">' + WRAPPER
            text += '    <link rel="canonical" href="{}" />'.format(page_url) + WRAPPER
        text += '    <link rel="icon" href="{}image/sakai-it.ico">'.format(relateive_prefix) + WRAPPER
        text += '    <link rel="apple-touch-icon" href="{}image/sakai-it.ico" sizes="180x180">'.format(relateive_prefix) + WRAPPER
        text += '    <meta name="viewport" content="width=device-width, initial-scale=1">' + WRAPPER
        text += '    <meta name="description" content="{}">'.format(head_infomation_map['blog_description']) + WRAPPER
        text += '    <title>{}</title>'.format(page_title) + WRAPPER
        text += '    <link rel="stylesheet" type="text/css" href="{}style/hf.css" />'.format(relateive_prefix) + WRAPPER
        if is_index:
            text += '    <link rel="stylesheet" type="text/css" href="style/index.css" />' + WRAPPER
            text += '    <link rel="stylesheet" type="text/css" href="style/aside.css" />' + WRAPPER
            with open(build_root_path + '/google_analytics/google_analytics.txt', 'r', encoding='UTF-8') as ga:
                text += ga.read()
        elif is_search_result:
            text += '    <link rel="stylesheet" type="text/css" href="{}style/index.css" />'.format(relateive_prefix) + WRAPPER
        else:
            text += '    <link rel="stylesheet" type="text/css" href="{}style/article.css" />'.format(relateive_prefix) + WRAPPER
            text += '    <link rel="stylesheet" type="text/css" href="{}style/aside.css" />'.format(relateive_prefix) + WRAPPER
        text += '</head>' + WRAPPER
        return text

    @classmethod
    def __get_html_from_second_line_to_end(cls, file_full_path):
        """
        for excludion css link in for each files
        """
        with open(file_full_path, 'r', encoding='UTF-8') as f:
            target_contents_list = f.read().split('\n')[1:]
        return '\n'.join(target_contents_list)

    @classmethod
    def __get_article_relative_url(cls, relative_path_prefix, head_infomation_map, meta_infomation_map, article_file_path):
        '''
        relative_path_prefix = '' '../' or '../../'
        '''
        absolute_url = cls.__get_article_absolute_url(head_infomation_map, meta_infomation_map=meta_infomation_map, article_file_path=article_file_path)
        return absolute_url.replace(head_infomation_map['blog_root_url'], relative_path_prefix)
    @classmethod
    def __get_article_absolute_url(cls, head_infomation_map, meta_infomation_map, article_file_path):
        category = meta_infomation_map['tags'].split(',')[0]
        category_en = cls.__get_tag_en(category)
        return '{}{}/{}/{}'.format(head_infomation_map['blog_root_url'], OUTPUT_ARTICLE_DIRECTORY_NAME, category_en, os.path.basename(article_file_path))
    @classmethod
    def __get_article_mata_infomation(cls, article_file_path):
        with open(article_file_path, 'r', encoding='UTF-8') as f:
            content = f.read().split('\n')
        result = {}
        for line in content:
            kv = line.split('\t')
            result[kv[0]] = kv[1]
        return result
    @classmethod
    def __get_index_article_block(cls, article_file_path, head_infomation_map, meta_infomation_map, relative_path_prefix):
        post_date_parts = meta_infomation_map['post_date'].split('-')
        post_date = datetime.date(int(post_date_parts[0]), int(post_date_parts[1]), int(post_date_parts[2]))

        image_link = '{}image/index/{}'.format(relative_path_prefix, meta_infomation_map['article_image_filename'])
        article_link = cls.__get_article_relative_url(relative_path_prefix, head_infomation_map=head_infomation_map, meta_infomation_map=meta_infomation_map, article_file_path=article_file_path)

        index_build_result_text = ''
        index_build_result_text += '        <div class="article-block">' + WRAPPER
        index_build_result_text += '            <div class="article-column">' + WRAPPER
        index_build_result_text += '                <a href="{}">'.format(article_link) + WRAPPER
        index_build_result_text += '                    <img class="article-image" src="{}" alt="{}"/>'.format(image_link, os.path.basename(meta_infomation_map['article_image_filename']).split('.')[0]) + WRAPPER
        index_build_result_text += '                </a>' + WRAPPER
        index_build_result_text += '            </div>' + WRAPPER
        index_build_result_text += '            <div class="article-column">' + WRAPPER
        index_build_result_text += '                <h3>' + WRAPPER
        index_build_result_text += '                    <a href="{}">'.format(article_link) + WRAPPER
        index_build_result_text += '                        {}'.format(meta_infomation_map['article_title']) + WRAPPER
        index_build_result_text += '                    </a>' + WRAPPER
        index_build_result_text += '                </h3>' + WRAPPER
        index_build_result_text += '                <p>' + WRAPPER
        index_build_result_text += '                    投稿日：{}年{}月{}日'.format(post_date.year, post_date.month, post_date.day) + WRAPPER
        index_build_result_text += '                </p>' + WRAPPER
        index_build_result_text += '                <ul class="tags">' + WRAPPER
        for tag in meta_infomation_map['tags'].split(','):
            index_build_result_text += cls.__write_tag_link(tag, is_index=(relative_path_prefix == RELATIVE_PREFIX_INDEX))
        index_build_result_text += '                </ul>' + WRAPPER
        index_build_result_text += '            </div>' + WRAPPER
        index_build_result_text += '        </div>' + WRAPPER
        return index_build_result_text
    @classmethod
    def __get_tag_en(cls, tag):
        if tag in tag_ens:
            return tag_ens[tag]
        else:
            return tag.lower().replace(' ', '_')
    @classmethod
    def __write_tag_link(cls, tag, is_index):
        tag_en = cls.__get_tag_en(tag)
        if is_index:
            link = '{}/{}/'.format(OUTPUT_SEARCH_DIRECTORY_NAME, tag_en)
        else:
            link = '../{}/'.format(tag_en)
        tag_link_text = ''
        tag_link_text += '        <li class="tag">' + WRAPPER
        tag_link_text += '            <a href="{}" rel="tag">'.format(link) + WRAPPER
        tag_link_text += '                {}'.format(tag) + WRAPPER
        tag_link_text += '            </a>' + WRAPPER
        tag_link_text += '        </li>' + WRAPPER
        return tag_link_text
    @classmethod
    def __write_pankuzu_list_html(cls, href_value__display_text__map_list):
        position_no = 1
        pankuzu_html = ''
        #pankuzu_html += '<div id="breadcrumbList" itemscope itemtype="http://schema.org/BreadcrumbList">' + WRAPPER
        pankuzu_html += '<div id="breadcrumbList" itemscope itemtype="http://schema.org/BreadcrumbList">' + WRAPPER
        for href_value__display_text__map in href_value__display_text__map_list:
            if 'href_value' in href_value__display_text__map and href_value__display_text__map['href_value'] is not None:
                pankuzu_html += '    <div class="breadcrumb" itemprop="itemListElement" itemscope itemtype="http://schema.org/ListItem">' + WRAPPER
                pankuzu_html += '        <a href="{}" itemprop="item">'.format(href_value__display_text__map['href_value']) + WRAPPER
                pankuzu_html += '             <span itemprop="name">{}</span>'.format(href_value__display_text__map['display_text']) + WRAPPER
                pankuzu_html += '        </a>' + WRAPPER
                pankuzu_html += '        <meta itemprop="position" content="{}" />'.format(position_no) + WRAPPER
                position_no += 1
                pankuzu_html += '    </div>' + WRAPPER
            else:
                pankuzu_html += '    <div class="breadcrumb">' + WRAPPER
                pankuzu_html += '        <span>{}</span>'.format(href_value__display_text__map['display_text']) + WRAPPER
                pankuzu_html += '    </div>' + WRAPPER
        pankuzu_html += '</div>' + WRAPPER
        #pankuzu_html += '</div>' + WRAPPER
        return pankuzu_html
    @classmethod
    def __remove_before_run(cls, build_root_path):
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
    def __get_aside_html(cls, build_root_path, is_index):
        text = '<aside role="complementary" itemscope itemtype="http://schema.org/WPSideBar">' + WRAPPER
        if is_index:
            text += '    <div id="about-this-website">' + WRAPPER
            text += '        <h2>このサイトについて</h2>' + WRAPPER
            text += '        <p>' + WRAPPER
            text += '             <a href="https://www.sakai-sc.co.jp/" target="_blank" rel="noopener noreferrer">堺財経電算合同会社</a>が運営するブログメディアサイトです。業務の一環として、中小企業の経営×IT活用術やプログラミングの話題を中心に発信しています。' + WRAPPER
            text += '        </p>' + WRAPPER
            text += '        <p>' + WRAPPER
            text += '             経営コンサルティング全般からシステム設計、コーディングまで最前線で何でもこなしている、代表者の堺が執筆しています。' + WRAPPER
            text += '        </p>' + WRAPPER
            text += '        <p>' + WRAPPER
            text += '             是非ご一読のほどよろしくお願いします。' + WRAPPER
            text += '        </p>' + WRAPPER
            text += '    </div>' + WRAPPER
        text += cls.__get_html_from_second_line_to_end(build_root_path + '/common_parts/author.html') + WRAPPER
        text += '</aside>' + WRAPPER
        if is_index:
            text = text.replace('../', '')
        return text
    @classmethod
    def __sitemap_builder(cls, head_infomation_map, articles):
        text = '<?xml version="1.0" encoding="UTF-8"?>' + WRAPPER
        text += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' + WRAPPER
        text += '<url>' + WRAPPER
        text += '   <loc>{}</loc>'.format(head_infomation_map['blog_root_url']) + WRAPPER
        text += '   <priority>1.0</priority>' + WRAPPER
        text += '</url>' + WRAPPER
        for article in articles:
            article_url = cls.__get_article_absolute_url(head_infomation_map, meta_infomation_map=article._meta_infomation_map, article_file_path=article._article_file_path)
            text += '<url>' + WRAPPER
            text += f'   <loc>{article_url}</loc>' + WRAPPER
            text += '   <priority>0.8</priority>' + WRAPPER
            if article._update_date is not None:
                text += '    <lastmod>{}</lastmod>'.format(datetime.strptime(article._update_date, '%Y-%m-%d')) + WRAPPER
            else:
                text += '    <lastmod>{}</lastmod>'.format(datetime.strptime(article._post_date, '%Y-%m-%d')) + WRAPPER
            text += '</url>' + WRAPPER
        text += '</urlset>' + WRAPPER
        return text


if __name__ == '__main__':
    main()