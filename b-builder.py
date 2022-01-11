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
PICKUP_TAGS = ['IT活用経営', '経営コンサルティング', 'プログラミング']
PUSH_CONTACT_TAGS = ['IT活用経営', '経営コンサルティング']

RELATIVE_PREFIX_ARTICLE = '../../'
RELATIVE_PREFIX_SEARCH = '../../'
RELATIVE_PREFIX_INDEX = ''

DESCRIPTION_LENGTH = 100

MARKDOWN_CODE_FLAG = '```'

WRAPPER = '\n'
tag_ens = {}


def main():
    build(sys.argv[1])

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
    aside_for_article = _PartsBuilder.get_aside_html(build_root_path, is_index=False, relative_prefix=RELATIVE_PREFIX_ARTICLE)
    aside_for_index = _PartsBuilder.get_aside_html(build_root_path, is_index=True, relative_prefix=RELATIVE_PREFIX_INDEX)
    footer = _PartsBuilder.get_html_from_second_line_to_end(build_root_path + '/common_parts/footer.html')
    head_infomation_map = _PartsBuilder.get_head_infomation_map(build_root_path)

    #article files
    article_list_wrapper = ArticleListWrapper(build_root_path=build_root_path)
    article_list_wrapper.save_article_files(head_infomation_map=head_infomation_map, header=header, aside=aside_for_article, footer=footer, output_directory_path=output_directory_path)

    #index file
    breadcrumbs_href_value__tag__map_list = []
    breadcrumbs_href_value__tag__map_list.append({'href_value':None, 'tag':PANKUZU_HOME_DISPLAY_TEXT})
    _PartsBuilder.save_index_or_search_file(build_root_path, head_infomation_map=head_infomation_map, articles=article_list_wrapper._articles, header=header, aside=aside_for_index, footer=footer, output_file_path=f'{output_directory_path}/index.html', display_title='◇新着記事', is_index=True, breadcrumbs_href_value__tag__map_list=breadcrumbs_href_value__tag__map_list)

    #build search files
    for tag, articles_with_the_tag in article_list_wrapper._tag_articles_map.items():
        breadcrumbs_href_value__tag__map_list = []
        breadcrumbs_href_value__tag__map_list.append({'href_value':head_infomation_map['blog_root_url'], 'tag':PANKUZU_HOME_DISPLAY_TEXT})
        breadcrumbs_href_value__tag__map_list.append({'href_value':None, 'tag':tag})

        tag_en = _PartsBuilder.get_tag_en(tag)
        tag_escaped = _PartsBuilder.tag_escaping(tag_en)
        save_dir = "{}/{}/{}".format(output_directory_path, OUTPUT_SEARCH_DIRECTORY_NAME, tag_escaped)
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)

        _PartsBuilder.save_index_or_search_file(build_root_path, head_infomation_map=head_infomation_map, articles=articles_with_the_tag, header=header, aside=aside_for_article, footer=footer, output_file_path=f'{save_dir}/index.html', display_title=f'{tag} を含む記事の一覧', is_index=False, breadcrumbs_href_value__tag__map_list=breadcrumbs_href_value__tag__map_list)

    #build sitemap
    sitemap_content = _PartsBuilder.sitemap_builder(head_infomation_map=head_infomation_map, article_list_wrapper=article_list_wrapper)
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
    def save_article_files(self, head_infomation_map, header, aside, footer, output_directory_path):
        for article in self._articles:
            articles_with_same_category, category_name = self.get_article_objects_and_tag_with_same_tag(article=article)
            article.save_article_file(build_root_path=self._build_root_path, article_list_wrapper=self, head_infomation_map=head_infomation_map, header=header, aside=aside, footer=footer, output_directory_path=output_directory_path, articles_with_same_category=articles_with_same_category, category_name=category_name)
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
        
class Article():
    def __init__(self, article_file_path, meta_infomation_map):
        self._article_file_path = article_file_path
        self._meta_infomation_map = meta_infomation_map
        post_date_parts = meta_infomation_map['post_date'].split('-')
        self._post_date = datetime.date(int(post_date_parts[0]), int(post_date_parts[1]), int(post_date_parts[2]))
        self._tags = meta_infomation_map["tags"].split(',')
        with open(self._article_file_path, 'r', encoding='UTF-8') as f:
            self._contents = f.read()
        self._description = self._contents[:DESCRIPTION_LENGTH * 3].replace('堺です。', '').replace('お疲れ様です。', '').replace('お世話様です。', '').replace('\n', '').replace('<strong>', '').replace('</strong>', '')[:DESCRIPTION_LENGTH - 2] + '...'
        if 'update_date' in meta_infomation_map:
            update_date_text_split = meta_infomation_map['update_date'].split(' ')[0].split('-')
            update_time_text_split = meta_infomation_map['update_date'].split(' ')[1].split(':')
            update_date = datetime.datetime(int(update_date_text_split[0]), int(update_date_text_split[1]), int(update_date_text_split[2]), int(update_time_text_split[0]), int(update_time_text_split[1]), 0)
            if update_date.day != self._post_date.day or update_date.month != self._post_date.month or update_date.year != self._post_date.year:
                self._update_date = update_date
            else:
                self._update_date = None

    def save_article_file(self, build_root_path, article_list_wrapper, head_infomation_map, header, aside, footer, output_directory_path, articles_with_same_category, category_name):
        article_build_result_text = _PartsBuilder.build_head(build_root_path, head_infomation_map=head_infomation_map, article=self) + WRAPPER
        article_build_result_text += '<body>' + WRAPPER
        article_build_result_text += header.replace('h1', 'h2') + WRAPPER

        main_category = self._tags[0]
        main_category_en = _PartsBuilder.get_tag_en(main_category)
        href_value__tag__map_list = []
        href_value__tag__map_list.append({'href_value':head_infomation_map['blog_root_url'], 'tag':PANKUZU_HOME_DISPLAY_TEXT})
        href_value__tag__map_list.append({'href_value':'{}{}/{}/'.format(head_infomation_map['blog_root_url'], OUTPUT_SEARCH_DIRECTORY_NAME, main_category_en), 'tag':main_category})
        href_value__tag__map_list.append({'href_value':None, 'tag':'本記事'})
        article_build_result_text += _PartsBuilder.write_pankuzu_list_html(href_value__tag__map_list)
        image_link = '../../image/index/{}'.format(self._meta_infomation_map['article_image_filename'])

        article_build_result_text += '<main id="main" itemprop="mainContentOfPage" itemscope itemtype="http://schema.org/Blog">' + WRAPPER
        article_build_result_text += '<article itemscope itemtype="http://schema.org/BlogPosting" itemprop="blogPost">' + WRAPPER
        article_build_result_text += '<h1 itemprop="name headline">' + WRAPPER
        article_build_result_text += '    {}'.format(self._meta_infomation_map['article_title'].replace('】', '】<br>').replace('（', '<br><span class="title-weak">（').replace('）', '）</span>').replace(' - ', '<br>')) + WRAPPER
        article_build_result_text += '</h1>' + WRAPPER
        article_build_result_text += '<div id="article-header">' + WRAPPER
        article_build_result_text += '    <div id="article-header-image">' + WRAPPER
        article_build_result_text += f'        <img class="article-image" src="{image_link}" alt="記事イメージ"/>' + WRAPPER
        article_build_result_text += '    </div>' + WRAPPER
        article_build_result_text += '    <p>' + WRAPPER
        article_build_result_text += '        {}年{}月{}日'.format(self._post_date.year, self._post_date.month, self._post_date.day) + WRAPPER
        if self._update_date is not None:
            article_build_result_text += '        <br>（最終更新日：{}年{}月{}日）'.format(self._update_date.year, self._update_date.month, self._update_date.day) + WRAPPER
        article_build_result_text += '    </p>' + WRAPPER
        article_build_result_text += '    <ul class="tags" itemprop="keywords">' + WRAPPER

        for tag in self._tags:
            article_build_result_text += _PartsBuilder.write_tag_link(tag=tag, is_index=False) + WRAPPER

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
        ad_added = False
        table_of_contents_witten = False
        subtitle_counter = 1
        has_syntax_highlight = False
        need_to_write_purpose = True

        for i in range(len(lines)):
            line = lines[i]

            # if not code_now and ' href="!' in line:
            #     #internal link exchange
            #     for article in article_list_wrapper._articles:
            #         href = f' href="!{os.path.basename(article._article_file_path)}"'
            #         if href in line:
            #             relative_article_internal_link = _PartsBuilder.get_article_relative_url(RELATIVE_PREFIX_ARTICLE, head_infomation_map=head_infomation_map, article=article)
            #             line = line.replace(href, f' href="{relative_article_internal_link}"')

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
                    elif line.startswith('#結び') and not ad_added:
                        ad_added = True
                        with open(build_root_path + '/common_parts/google_ad_inline.txt', 'r', encoding='UTF-8') as f:
                            text += f.read()
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
                article = list(filter(lambda x: os.path.basename(x._article_file_path).replace('.html', '') == line[1:], article_list_wrapper._articles))[0]
                relative_article_internal_link = _PartsBuilder.get_article_relative_url(RELATIVE_PREFIX_ARTICLE, head_infomation_map=head_infomation_map, article=article)
                text += '<div class="related-article">' + WRAPPER
                text += f'    <span>関連記事：<a href="{relative_article_internal_link}">{article._meta_infomation_map["article_title"]}</a></span>' + WRAPPER
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
        text += '</div>' + WRAPPER


        #article_build_result_text += text.replace('<strong>', '<span class="strong">').replace('</strong>', '</span>')
        article_build_result_text += text

        article_absolute_url = _PartsBuilder.get_article_absolute_url(head_infomation_map=head_infomation_map, article=self)
        article_title_quote = urllib.parse.quote(self._meta_infomation_map["article_title"])

        if not ad_added:
            with open(build_root_path + '/common_parts/google_ad_inline.txt', 'r', encoding='UTF-8') as f:
                article_build_result_text += f.read()

        article_build_result_text += f'<a href="https://www.sakai-sc.co.jp/lp/it/" target="_blank" rel="noopener noreferrer"><img src="{RELATIVE_PREFIX_ARTICLE}image/lp-banner.webp" alt="IT活用経営を実現する - 堺財経電算合同会社" style="width: 100%; margin: 10px 0 10px 0;"></a>' + WRAPPER
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

        related_article_text = '<div id="news">' + WRAPPER
        related_article_text += f'    <h2>「{category_name}」の関連記事</h2>' + WRAPPER
        related_article_count = 0
        for article_with_same_categpty in articles_with_same_category:
            related_article_text += _PartsBuilder.get_index_article_block(head_infomation_map=head_infomation_map, article=article_with_same_categpty, relative_path_prefix='../../') + WRAPPER
            if related_article_count == 4:
                break
            else:
                related_article_count += 1
        related_article_text += '</div>' + WRAPPER
        if related_article_count > 0:
            article_build_result_text += related_article_text
            article_build_result_text += '<p class="other-articles-link-box">'
            article_build_result_text += f'    <a href="../{_PartsBuilder.tag_escaping(_PartsBuilder.get_tag_en(category_name))}/" class="other-articles-link">'
            article_build_result_text += f'        「{category_name}」の関連記事をもっと見る'
            article_build_result_text += '    </a>'
            article_build_result_text += '</p>'
        if category_name != main_category:
            article_build_result_text += '<p>'
            article_build_result_text += f'    <a href="../{_PartsBuilder.tag_escaping(_PartsBuilder.get_tag_en(main_category))}/" class="other-articles-link">'
            article_build_result_text += f'        「{main_category}」の関連記事をもっと見る'
            article_build_result_text += '    </a>'
            article_build_result_text += '</p>'

        article_build_result_text += '</article>' + WRAPPER
        article_build_result_text += aside + WRAPPER
        article_build_result_text += '</main>'
        article_build_result_text += footer + WRAPPER
        article_build_result_text += _PartsBuilder.body_end_scripts(has_syntax_highlight=has_syntax_highlight, relateive_prefix=RELATIVE_PREFIX_ARTICLE)
        article_build_result_text += '</body>' + WRAPPER
        article_build_result_text += '</html>' + WRAPPER
        output_path = "{}/{}/{}".format(output_directory_path, OUTPUT_ARTICLE_DIRECTORY_NAME, _PartsBuilder.get_tag_en(self._tags[0]))
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        with open("{}/{}".format(output_path, os.path.basename(self._article_file_path)), mode="w", encoding='UTF-8') as f:
            f.write(article_build_result_text)


class _PartsBuilder:
    @classmethod
    def build_head(cls, build_root_path, head_infomation_map, article=None, is_index=False, is_search_result=False, tag=None):
        now = datetime.datetime.now()
        deploy_timestamp = f'deploy-id={now.year + now.month + now.day + now.hour + now.minute + now.second}'
        if is_index:
            relateive_prefix = RELATIVE_PREFIX_INDEX
            page_title = "{} | {}".format(head_infomation_map['blog_title'], head_infomation_map['blog_subtitle'])
            page_url = head_infomation_map['blog_root_url']
        elif is_search_result:
            relateive_prefix = RELATIVE_PREFIX_SEARCH
            page_title = "{} を含む記事一覧 | {}".format(tag, head_infomation_map['blog_title'])
            page_url = '{}{}/{}/'.format(head_infomation_map['blog_root_url'], OUTPUT_SEARCH_DIRECTORY_NAME, cls.get_tag_en(tag))
        else:
            relateive_prefix = RELATIVE_PREFIX_ARTICLE
            page_title = "{} | {}".format(article._meta_infomation_map['article_title'], head_infomation_map['blog_title'])
            page_url = cls.get_article_absolute_url(head_infomation_map=head_infomation_map, article=article)

        if article is not None:
            description = article._description
        else:
            description = head_infomation_map['blog_description']

        text = '<!DOCTYPE html>' + WRAPPER
        text += '<html lang="ja" prefix="og: http://ogp.me/ns#">' + WRAPPER
        text += '<head>' + WRAPPER
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
        text += '    <meta property="og:image" content="{}" />'.format(head_infomation_map['og_image']) + WRAPPER
        text += '    <meta name="twitter:card" content="summary_large_image"/>' + WRAPPER
        text += '    <meta name="twitter:site" content="{}"/>'.format(head_infomation_map['twitter_site']) + WRAPPER
        text += '    <meta name="twitter:creator" content="{}"/>'.format(head_infomation_map['twitter_creator']) + WRAPPER
        text += '    <meta name="twitter:title" content="{}"/>'.format(page_title) + WRAPPER
        text += '    <meta name="twitter:description" content="{}"/>'.format(description) + WRAPPER
        text += '    <meta itemprop="name" content="堺財経電算合同会社">' + WRAPPER
        text += '    <meta itemprop="url" content="https://www.sakai-sc.co.jp/">' + WRAPPER
        text += '    <meta itemprop="about" content="堺財経電算合同会社は、「ITエンジニアリング」と「経営コンサルティング」の2つの知見を併せ持つプロフェッショナルとしてお客様をサポートいたします。">' + WRAPPER
        text += '    <link rel="canonical" href="{}" />'.format(page_url) + WRAPPER
        text += '    <link rel="icon" href="{}image/sakai-it.ico">'.format(relateive_prefix) + WRAPPER
        text += '    <link rel="apple-touch-icon" href="{}image/sakai-it.ico" sizes="180x180">'.format(relateive_prefix) + WRAPPER
        text += '    <meta name="viewport" content="width=device-width, initial-scale=1">' + WRAPPER
        text += '    <meta name="description" content="{}">'.format(description) + WRAPPER
        text += '    <title>{}</title>'.format(page_title) + WRAPPER
        text += '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3705637168814299"' + WRAPPER
        text += '    crossorigin="anonymous"></script>' + WRAPPER
        text += '    <link rel="stylesheet" type="text/css" href="{}style/hf.css?{}" />'.format(relateive_prefix, deploy_timestamp) + WRAPPER
        text += '    <link rel="stylesheet" type="text/css" href="{}style/aside.css?{}" />'.format(relateive_prefix, deploy_timestamp) + WRAPPER
        if is_index:
            text += '    <link rel="stylesheet" type="text/css" href="{}style/index.css?{}" />'.format(relateive_prefix, deploy_timestamp) + WRAPPER
        elif is_search_result:
            text += '    <link rel="stylesheet" type="text/css" href="{}style/index.css?{}" />'.format(relateive_prefix, deploy_timestamp) + WRAPPER
            if not tag in PICKUP_TAGS:
                text += '    <meta name="robots" content="noindex">' + WRAPPER
        else:
            now = datetime.datetime.now()
            text += '    <link rel="stylesheet" type="text/css" href="{}style/article.css?{}" />'.format(relateive_prefix, deploy_timestamp) + WRAPPER
        with open(build_root_path + '/google_analytics/google_analytics.txt', 'r', encoding='UTF-8') as ga:
            text += ga.read()
        text += '</head>' + WRAPPER
        return text

    @classmethod
    def save_index_or_search_file(cls, build_root_path, head_infomation_map, articles, header, aside, footer, output_file_path, display_title, is_index, breadcrumbs_href_value__tag__map_list):
        if is_index:
            relative_path_prefix = RELATIVE_PREFIX_INDEX
            tag = None
        else:
            relative_path_prefix = RELATIVE_PREFIX_SEARCH
            tag = breadcrumbs_href_value__tag__map_list[len(breadcrumbs_href_value__tag__map_list) - 1]['tag']

        index_build_result_text = cls.build_head(build_root_path, head_infomation_map=head_infomation_map, is_index=is_index, is_search_result=not is_index, tag=tag)
        index_build_result_text += '<body>' + WRAPPER
        if is_index:
            index_build_result_text += header.replace('../', '') + WRAPPER
        else:
            index_build_result_text += header + WRAPPER
        index_build_result_text += '<p id="site-descriptopn-display">' + WRAPPER
        index_build_result_text += f'    {head_infomation_map["blog_description"]}' + WRAPPER
        index_build_result_text += '</p>' + WRAPPER
        index_build_result_text += cls.write_pankuzu_list_html(breadcrumbs_href_value__tag__map_list) + WRAPPER
        index_build_result_text += '<main id="main" itemprop="mainContentOfPage" itemscope itemtype="http://schema.org/Blog">' + WRAPPER
        index_build_result_text += '    <div id="news-box">' + WRAPPER
        index_build_result_text += f'        <h2 class="column-title">{display_title}</h2>' + WRAPPER
        index_build_result_text += '        <div id="news">' + WRAPPER
        for article in articles:
            index_build_result_text += cls.get_index_article_block(head_infomation_map=head_infomation_map, article=article, relative_path_prefix=relative_path_prefix)
        index_build_result_text += '        </div>' + WRAPPER
        index_build_result_text += '    </div>' + WRAPPER
        if is_index:
            index_build_result_text += aside.replace('../', '')
        else:
            index_build_result_text += aside
        index_build_result_text += '</main>' + WRAPPER
        index_build_result_text += footer + WRAPPER
        index_build_result_text += cls.body_end_scripts(has_syntax_highlight=False, relateive_prefix=relative_path_prefix)
        index_build_result_text += '</body>' + WRAPPER
        index_build_result_text += '</html>' + WRAPPER
        with open(output_file_path, mode="w", encoding='UTF-8') as f:
            f.write(index_build_result_text)

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
    def get_article_relative_url(cls, relative_path_prefix, head_infomation_map, article):
        '''
        relative_path_prefix = '' '../' or '../../'
        '''
        absolute_url = cls.get_article_absolute_url(head_infomation_map, article)
        return absolute_url.replace(head_infomation_map['blog_root_url'], relative_path_prefix)
    @classmethod
    def get_article_absolute_url(cls, head_infomation_map, article):
        category_en = cls.get_tag_en(article._tags[0])
        return '{}{}/{}/{}'.format(head_infomation_map['blog_root_url'], OUTPUT_ARTICLE_DIRECTORY_NAME, category_en, os.path.basename(article._article_file_path))
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
    def get_index_article_block(cls, head_infomation_map, article, relative_path_prefix):
        image_link = '{}image/index/{}'.format(relative_path_prefix, article._meta_infomation_map['article_image_filename'])
        article_link = cls.get_article_relative_url(relative_path_prefix, head_infomation_map=head_infomation_map, article=article)

        index_build_result_text = ''
        index_build_result_text += '        <div class="article-block">' + WRAPPER
        index_build_result_text += '            <div class="article-column">' + WRAPPER
        index_build_result_text += f'                <a href="{article_link}"><img class="article-image" src="{image_link}" alt="{article._meta_infomation_map["article_title"]}"/></a>' + WRAPPER
        index_build_result_text += '            </div>' + WRAPPER
        index_build_result_text += '            <div class="article-column">' + WRAPPER
        index_build_result_text += '                <h3>' + WRAPPER
        index_build_result_text += f'                    <a href="{article_link}">{article._meta_infomation_map["article_title"]}</a>' + WRAPPER
        index_build_result_text += '                </h3>' + WRAPPER
        index_build_result_text += '                <p>' + WRAPPER
        index_build_result_text += '                    投稿日：{}年{}月{}日'.format(article._post_date.year, article._post_date.month, article._post_date.day) + WRAPPER
        if article._update_date is not None:
            index_build_result_text += '        <br>最終更新日：{}年{}月{}日'.format(article._update_date.year, article._update_date.month, article._update_date.day) + WRAPPER
        index_build_result_text += '                </p>' + WRAPPER
        index_build_result_text += '                <ul class="tags">' + WRAPPER
        for tag in article._tags:
            index_build_result_text += cls.write_tag_link(tag, is_index=(relative_path_prefix == RELATIVE_PREFIX_INDEX))
        index_build_result_text += '                </ul>' + WRAPPER
        index_build_result_text += '            </div>' + WRAPPER
        index_build_result_text += '        </div>' + WRAPPER
        return index_build_result_text

    @classmethod
    def body_end_scripts(cls, has_syntax_highlight, relateive_prefix):
        text = ''
        if has_syntax_highlight:
            text += '    <script src="{}js/highlight.min.js"></script>'.format(relateive_prefix) + WRAPPER
            text += '    <link rel="stylesheet" type="text/css" href="{}style/tomorrow-night-bright.min.css"/>'.format(relateive_prefix) + WRAPPER
            text += '    <script type="text/javascript">' + WRAPPER
            text += '        hljs.initHighlightingOnLoad();' + WRAPPER
            text += '    </script>' + WRAPPER
        text += '    <script>' + WRAPPER
        text += '        (adsbygoogle = window.adsbygoogle || []).push({});' + WRAPPER
        text += '        (adsbygoogle = window.adsbygoogle || []).push({});' + WRAPPER
        if relateive_prefix != RELATIVE_PREFIX_INDEX:
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
    def write_tag_link(cls, tag, is_index):
        tag_en = cls.get_tag_en(tag)
        tag_escaped = cls.tag_escaping(tag_en)
        tag_for_display = cls.tag_display(tag)
        if is_index:
            link = '{}/{}/'.format(OUTPUT_SEARCH_DIRECTORY_NAME, tag_escaped)
        else:
            link = '../{}/'.format(tag_escaped)
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
    def get_aside_html(cls, build_root_path, is_index, relative_prefix):
        text = '<aside role="complementary" itemscope itemtype="http://schema.org/WPSideBar">' + WRAPPER
        text += '    <div id="about-this-website">' + WRAPPER
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
        #text += '    <span style="color:gray;font-size:15px;">スポンサーリンク</span>' + WRAPPER
        with open(build_root_path + '/common_parts/google_ad_vertical.txt', 'r', encoding='UTF-8') as f:
            text += f.read()
        text += f'    <a href="https://www.sakai-sc.co.jp/lp/it/" target="_blank" rel="noopener noreferrer"><img src="{relative_prefix}image/lp-square.webp" alt="IT活用経営を実現する - 堺財経電算合同会社" style="width: 100%;margin: 20px 0 20px 0;"></a>' + WRAPPER
        text += '</aside>' + WRAPPER
        if is_index:
            text = text.replace('../', '')
        return text
    @classmethod
    def sitemap_builder(cls, head_infomation_map, article_list_wrapper):
        text = '<?xml version="1.0" encoding="UTF-8"?>' + WRAPPER
        text += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' + WRAPPER
        text += '<url>' + WRAPPER
        text += '   <loc>{}</loc>'.format(head_infomation_map['blog_root_url']) + WRAPPER
        text += '   <priority>1.0</priority>' + WRAPPER
        text += '</url>' + WRAPPER
        for article in article_list_wrapper._articles:
            article_url = cls.get_article_absolute_url(head_infomation_map=head_infomation_map, article=article)
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
            text += f'   <loc>{head_infomation_map["blog_root_url"]}{OUTPUT_ARTICLE_DIRECTORY_NAME}/{_PartsBuilder.get_tag_en(tag)}/</loc>' + WRAPPER
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

if __name__ == '__main__':
    main()
