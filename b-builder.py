import datetime
import glob
import os
import sys

OUTPUT_OUTPUT_DIRECTORY_NAME = 'output'
OUTPUT_ARTICLE_DIRECTORY_NAME = 'article'
OUTPUT_SEARCH_DIRECTORY_NAME = 'search'
WRAPPER = '\n'
tag_ens = {}

def main():
    build(sys.argv[1])

def build(build_root_path):
    __remove_before_run(build_root_path)
    output_directory_path = '{}/{}'.format(build_root_path, OUTPUT_OUTPUT_DIRECTORY_NAME)
    with open(build_root_path + '/tag_en.txt', 'r', encoding='UTF-8') as f:
        for line in f.read().split('\n'):
            kv = line.split('\t')
            tag_ens[kv[0]] = kv[1].lower()
    header = __get_html_from_second_line_to_end(build_root_path + '/common_parts/header.html')
    aside = __get_html_from_second_line_to_end(build_root_path + '/common_parts/aside.html')
    footer = __get_html_from_second_line_to_end(build_root_path + '/common_parts/footer.html')
    
    head_infomation_map = __get_head_infomation_map(build_root_path)

    article_html_files_path = glob.glob(build_root_path + "/articles/*.html")
    article_meta_files_path = glob.glob(build_root_path + "/articles/*.txt")

    if not os.path.exists(output_directory_path):
        os.makedirs(output_directory_path)
    if not os.path.exists(output_directory_path + '/' + OUTPUT_ARTICLE_DIRECTORY_NAME):
        os.makedirs(output_directory_path + '/' + OUTPUT_ARTICLE_DIRECTORY_NAME)
    if not os.path.exists(output_directory_path + '/' + OUTPUT_SEARCH_DIRECTORY_NAME):
        os.makedirs(output_directory_path + '/' + OUTPUT_SEARCH_DIRECTORY_NAME)

    tag_article_filenames_map = {}
    article_path_mata_infomation_map = {}
    article_file_path_post_date_map_list = []

    #get var article_file_path_post_date_map_list_orderby_post_date_desc
    for article_file_path in article_html_files_path:
        meta_infomation_file_path = list(filter(lambda x: os.path.basename(x) == os.path.basename(article_file_path).replace('.html', '.txt'), article_meta_files_path))[0]
        meta_infomation_map = __get_article_mata_infomation(meta_infomation_file_path)
        post_date_parts = meta_infomation_map['post_date'].split('-')
        post_date = datetime.date(int(post_date_parts[0]), int(post_date_parts[1]), int(post_date_parts[2]))
        
        article_path_mata_infomation_map[article_file_path] = meta_infomation_map
        article_file_path_post_date_map_list.append({'file_path':article_file_path, 'post_date':post_date})
    article_file_path_post_date_map_list_orderby_post_date_desc = sorted(article_file_path_post_date_map_list, key=lambda x:x['post_date'], reverse=True)
    #create articles html
    for article_file_path in article_html_files_path:
        #meta_infomation_file_path = list(filter(lambda x: os.path.basename(x) == os.path.basename(article_file_path).replace('.html', '.txt'), article_meta_files_path))[0]
        meta_infomation_map = article_path_mata_infomation_map[article_file_path]
        post_date_parts = meta_infomation_map['post_date'].split('-')
        post_date = datetime.date(int(post_date_parts[0]), int(post_date_parts[1]), int(post_date_parts[2]))
    
        article_build_result_text = __build_head(build_root_path, head_infomation_map=head_infomation_map, is_index=False, article_file_name_without_extention=os.path.basename(article_file_path).replace('.html', ''), article_title=meta_infomation_map['article_title']) + WRAPPER
        article_build_result_text += header + WRAPPER
        article_build_result_text += '<main id="main" itemprop="mainContentOfPage" itemscope="itemscope" itemtype="http://schema.org/Blog">' + WRAPPER
        article_build_result_text += '<article itemscope="itemscope" itemtype="http://schema.org/BlogPosting" itemprop="blogPost">' + WRAPPER
        article_build_result_text += '<div id="article-header">' + WRAPPER
        article_build_result_text += '    <h1 itemprop="name headline">' + WRAPPER
        article_build_result_text += '        {}'.format(meta_infomation_map['article_title_with_br']) + WRAPPER
        article_build_result_text += '    </h1>' + WRAPPER
        article_build_result_text += '    <p>' + WRAPPER
        article_build_result_text += '        {}年{}月{}日'.format(post_date.year, post_date.month, post_date.day) + WRAPPER
        article_build_result_text += '    </p>' + WRAPPER
        article_build_result_text += '    <ul class="tags" itemprop="keywords" class="keywords">' + WRAPPER
        for tag in meta_infomation_map['tags'].split(','):
            article_build_result_text += __write_tag_link(tag, False)
            if tag in tag_article_filenames_map:
                tag_article_filenames_map[tag].append(os.path.basename(article_file_path))
            else:
                tag_article_filenames_map[tag] = [os.path.basename(article_file_path)]
        article_build_result_text += '    </ul>' + WRAPPER
        article_build_result_text += '</div>' + WRAPPER
        article_build_result_text += __get_article_main_html(article_file_path, head_infomation_map, meta_infomation_map, article_file_path_post_date_map_list_orderby_post_date_desc) + WRAPPER
        article_build_result_text += aside + WRAPPER
        article_build_result_text += '</main>'
        article_build_result_text += footer + WRAPPER
        with open("{}/{}/{}".format(output_directory_path, OUTPUT_ARTICLE_DIRECTORY_NAME, os.path.basename(article_file_path)), mode="w", encoding='UTF-8') as f:
            f.write(article_build_result_text)
    

    #build index html
    index_build_result_text = __build_head(build_root_path, head_infomation_map=head_infomation_map, is_index=True)
    index_build_result_text += header + WRAPPER
    index_build_result_text += '<main id="main" itemprop="mainContentOfPage" itemscope="itemscope" itemtype="http://schema.org/Blog">' + WRAPPER
    index_build_result_text += '    <h2>新着記事</h2>' + WRAPPER
    index_build_result_text += '    <div id="news">' + WRAPPER
    for article_file_path_post_date_map in article_file_path_post_date_map_list_orderby_post_date_desc:
        article_filename = os.path.basename(article_file_path_post_date_map['file_path'])
        meta_infomation_file_path = list(filter(lambda x: os.path.basename(x) == article_filename.replace('.html', '.txt'), article_meta_files_path))[0]
        meta_infomation_map = article_path_mata_infomation_map[article_file_path_post_date_map['file_path']]
        index_build_result_text += __get_index_article_block(article_filename, meta_infomation_map=meta_infomation_map, is_index=True)
    index_build_result_text += '    </div>'
    index_build_result_text += '</main>'
    index_build_result_text += footer
    with open("{}/index.html".format(output_directory_path), mode="w", encoding='UTF-8') as f:
        f.write(index_build_result_text)

    #build search files
    for tag, article_filenames in tag_article_filenames_map.items():
        tag_en = __get_tag_en(tag)
        search_build_result_text = __build_head(build_root_path, head_infomation_map=head_infomation_map, is_search_result=True, search_word=tag_en)
        search_build_result_text += header
        search_build_result_text += '<main id="main" itemprop="mainContentOfPage" itemscope="itemscope" itemtype="http://schema.org/Blog">' + WRAPPER
        search_build_result_text += '    <h2>{} を含む記事の検索結果</h2>'.format(tag) + WRAPPER
        search_build_result_text += '    <div id="news">' + WRAPPER
        for article_filename in article_filenames:
            article_file_path = list(filter(lambda x: os.path.basename(x) == article_filename, article_html_files_path))[0]
            meta_infomation_map = article_path_mata_infomation_map[article_file_path]
            search_build_result_text += __get_index_article_block(article_filename, meta_infomation_map=meta_infomation_map, is_index=False)
        search_build_result_text += '    </div>' + WRAPPER
        search_build_result_text += '</main>' + WRAPPER
        search_build_result_text += footer
        with open("{}/{}/{}.html".format(output_directory_path, OUTPUT_SEARCH_DIRECTORY_NAME, tag_en), mode="w", encoding='UTF-8') as f:
            f.write(search_build_result_text)

    #build sitemap
    sitemap_content = __sitemap_builder(head_infomation_map=head_infomation_map, article_path_mata_infomation_map=article_path_mata_infomation_map)
    with open("{}/{}/sitemap.xml".format(output_directory_path, OUTPUT_SEARCH_DIRECTORY_NAME), mode="w", encoding='UTF-8') as f:
        f.write(sitemap_content)

    print(f'output terminated in {output_directory_path}.')

def __get_head_infomation_map(build_root_path):
    with open(build_root_path + '/head-items.txt', 'r', encoding='UTF-8') as f:
        head_infomation_map_content = f.read().split('\n')
    result = {}
    for line in head_infomation_map_content:
        kv = line.split('\t')
        if len(kv) == 2:
            result[kv[0]] = kv[1]
    return result

def __build_head(build_root_path, head_infomation_map, is_index=False, is_search_result=False, article_file_name_without_extention=None, article_title=None, search_word=None):
    page_url = head_infomation_map['blog_root_url']
    if not page_url.endswith('/'):
        page_url += '/'

    if is_index:
        page_title = "{} | {}".format(head_infomation_map['blog_title'], head_infomation_map['blog_subtitle'])
    elif is_search_result:
        page_title = "{} の検索結果 | {}".format(search_word, head_infomation_map['blog_title'])
        page_url = f'{page_url}{OUTPUT_SEARCH_DIRECTORY_NAME}/{search_word}.html'
    else:
        page_title = "{} | {}".format(article_title, head_infomation_map['blog_title'])
        page_url = page_url + f'{OUTPUT_ARTICLE_DIRECTORY_NAME}/{article_file_name_without_extention}.html'

    text = '<!DOCTYPE html>' + WRAPPER
    text += '<html>' + WRAPPER
    text += '<meta charset="UTF-8">' + WRAPPER
    text += '<meta http-equiv="X-UA-Compatible" content="IE=edge">' + WRAPPER

    if is_search_result:
        text += '<meta name="robots" content="noindex">' + WRAPPER
    else:
        text += '<meta property="og:url" content="{}" />'.format(page_url) + WRAPPER
        text += '<meta property="og:title" content="{}" />'.format(page_title) + WRAPPER
        text += '<meta property="og:description" content="{}" />'.format(head_infomation_map['blog_description']) + WRAPPER
        text += '<meta property="og:site_name" content="{}" />'.format(head_infomation_map['blog_title']) + WRAPPER
        text += '<meta property="og:type" content="website" />' + WRAPPER
        text += '<meta property="og:image" content="{}" />'.format(head_infomation_map['og_image']) + WRAPPER
        text += '<meta name="twitter:card" value="summary_large_image"/>' + WRAPPER
        text += '<meta name="twitter:site" value="{}"/>'.format(head_infomation_map['twitter_site']) + WRAPPER
        text += '<meta name="twitter:creator" value="{}"/>'.format(head_infomation_map['twitter_creator']) + WRAPPER
        text += '<meta name="twitter:title" value="{}"/>'.format(page_title) + WRAPPER
        text += '<meta name="twitter:description" value="{}"/>'.format(head_infomation_map['blog_description']) + WRAPPER
        text += '<link rel="canonical" href="{}" />'.format(page_url) + WRAPPER

    if is_index:
        text += '<link rel="icon" href="image/sakai-it.ico">' + WRAPPER
        text += '<link rel="apple-touch-icon" href="image/sakai-it.ico" sizes="180x180">' + WRAPPER
    else:
        text += '<link rel="icon" href="../image/sakai-it.ico">' + WRAPPER
        text += '<link rel="apple-touch-icon" href="../image/sakai-it.ico" sizes="180x180">' + WRAPPER
    text += '<meta name="viewport" content="width=device-width, initial-scale=1">' + WRAPPER
    text += '<meta name="description" content="{}">'.format(head_infomation_map['blog_description']) + WRAPPER
    text += '<title>{}</title>'.format(page_title) + WRAPPER
    if is_index:
        text += '<link rel="stylesheet" type="text/css" href="style/hf.css" />' + WRAPPER
        text += '<link rel="stylesheet" type="text/css" href="style/index.css" />' + WRAPPER
        with open(build_root_path + '/google_analytics/google_analytics.txt', 'r', encoding='UTF-8') as ga:
            text += ga.read()
    elif is_search_result:
        text += '<link rel="stylesheet" type="text/css" href="../style/hf.css" />' + WRAPPER
        text += '<link rel="stylesheet" type="text/css" href="../style/index.css" />' + WRAPPER
    else:
        text += '<link rel="stylesheet" type="text/css" href="../style/hf.css" />' + WRAPPER
        text += '<link rel="stylesheet" type="text/css" href="../style/article.css" />' + WRAPPER
    text += '</head>' + WRAPPER
    return text


def __get_html_from_second_line_to_end(file_full_path):
    """
    for excludion css link in for each files
    """
    with open(file_full_path, 'r', encoding='UTF-8') as f:
        target_contents_list = f.read().split('\n')[1:]
    return '\n'.join(target_contents_list)


def __get_article_main_html(file_path, head_infomation_map, meta_infomation_map, article_file_path_post_date_map_list_orderby_post_date_desc):
    with open(file_path, 'r', encoding='UTF-8') as f:
        contents = f.read()
    text = '<div id="article-main">' + WRAPPER
    lines = contents.split('\n')
    titles = list(filter(lambda x: x.startswith('#') and x[1] != '#', lines))
    code_now = False
    table_of_contents_witten = False
    subtitle_counter = 1

    for i in range(len(lines)):
        line = lines[i]
        if line == '':
            continue
        tag = ''
        if line.startswith('#'):
            if line.startswith('##'):
                tag = 'h3'
                attibute = ''
            else:
                tag = f'h2'
                attibute = ' id="article-subtilte-{subtitle_counter}"'
                subtitle_counter += 1
                if not table_of_contents_witten:
                    table_of_contents_witten = True
                    text += '<div id="table-of-contents">'
                    text += '    <h3>'
                    text += '        ♦目次'
                    text += '    </h3>'
                    text += '    <ol>' + WRAPPER
                    for i in range(len(titles)):
                        text += '    <li>' + WRAPPER
                        text += f'        <a href="#article-subtilte-{i + 1}">{titles[i][1:]}</a>' + WRAPPER
                        text += '    </li>' + WRAPPER
                    text += '    </ol>' + WRAPPER
                    text += '</div>' + WRAPPER
            text += f'<{tag}{attibute}>{line[1:]}</{tag}>' + WRAPPER
        elif line.startswith('```'):
            if code_now:
                text += '</code></pre>' + WRAPPER
            else:
                text += '<pre><code>' + WRAPPER
            code_now = not code_now
        elif code_now:
            text += line + '\n'
        elif line.startswith('-'):
            if i == 0 or not lines[i - 1].startswith('-'):
                text += '<ul>'
            text += '    <li>{}</li>'.format(line[1:])
            if i == len(lines) - 1 or not lines[i + 1].startswith('-'):
                text += '</ul>'
        elif line.startswith('!'):
            img_info = line[1:].split('!')
            text += '<figure>' + WRAPPER
            text += f'    <figcaption>{img_info[1]}</figcaption>' + WRAPPER
            text += '    <img src="../image/{}/{}"/>'.format(os.path.basename(file_path).replace('.html', ''), img_info[0]) + WRAPPER
            text += '</figure>' + WRAPPER
        else:
            text += '<p>' + WRAPPER
            text += '    ' + line + WRAPPER
            text += '</p>' + WRAPPER
        text += WRAPPER
    text += '</div>' + WRAPPER

    article_url = head_infomation_map["blog_root_url"]
    if not article_url.endswith('/'):
        article_url += '/'
    article_url += f'{OUTPUT_ARTICLE_DIRECTORY_NAME}/{os.path.basename(file_path)}'

    text += '<div id="share_on_sns">' + WRAPPER
    text += '    <h2>SNSでシェア</h2>' + WRAPPER
    text += '    <ul id="sns_button">' + WRAPPER
    text += '        <li>' + WRAPPER
    text += f'            <a href="http://www.facebook.com/sharer.php?u={article_url}&amp;t={meta_infomation_map["article_title"]}" target="_blank">' + WRAPPER
    text += '                <div class="link-facebook">' + WRAPPER
    text += '                    <img class="sns-icon" src="../image/sns/f_logo_RGB-White_72.png">' + WRAPPER
    text += '                    <span>facebook</span>' + WRAPPER
    text += '                </div>' + WRAPPER
    text += '            </a>' + WRAPPER
    text += '        </li>' + WRAPPER
    text += '        <li>' + WRAPPER
    text += f'            <a href="http://twitter.com/share?text={meta_infomation_map["article_title"]}&url={article_url}" target="_blank">' + WRAPPER
    text += '                <div class="link-twitter">' + WRAPPER
    text += '                    <img class="sns-icon" src="../image/sns/2021 Twitter logo - white.png">' + WRAPPER
    text += '                    <span>Twitter</span>' + WRAPPER
    text += '                </div>' + WRAPPER
    text += '            </a>' + WRAPPER
    text += '        </li>' + WRAPPER
    text += '        <li>' + WRAPPER
    text += f'            <a href="http://b.hatena.ne.jp/add?mode=confirm&url={article_url}&title={meta_infomation_map["article_title"]}" target="_blank">' + WRAPPER
    text += '                <div class="link-hatebu">' + WRAPPER
    text += '                    <img class="sns-icon" src="../image/sns/b_hatena.png">' + WRAPPER
    text += '                    <span>hatebu</span>' + WRAPPER
    text += '                </div>' + WRAPPER
    text += '            </a>' + WRAPPER
    text += '        </li>' + WRAPPER
    text += '        <li>' + WRAPPER
    text += f'            <a href="http://line.naver.jp/R/msg/text/?{meta_infomation_map["article_title"]}%0D%0A{article_url}" target="_blank">' + WRAPPER
    text += '                <div class="link-line">' + WRAPPER
    text += '                    <img class="sns-icon" src="../image/sns/LINE_Brand_icon.png">' + WRAPPER
    text += '                    <span>LINE</span>' + WRAPPER
    text += '                </div>' + WRAPPER
    text += '            </a>' + WRAPPER
    text += '        </li>' + WRAPPER
    text += '        <li>' + WRAPPER
    text += f'            <a href="http://getpocket.com/edit?url={article_url}&title={meta_infomation_map["article_title"]}" target="_blank">' + WRAPPER
    text += '                <div class="link-pocket">' + WRAPPER
    text += '                    <img class="sns-icon" src="../image/sns/pocket.png">' + WRAPPER
    text += '                    <span>Read Later</span>' + WRAPPER
    text += '                </div>' + WRAPPER
    text += '            </a>' + WRAPPER
    text += '        </li>' + WRAPPER
    text += '    </ul>' + WRAPPER
    text += '</div>' + WRAPPER
    text += '<div id="news">' + WRAPPER
    text += '    <h2>新着記事</h2>' + WRAPPER
    for article_file_path_post_date_map in article_file_path_post_date_map_list_orderby_post_date_desc:
        current_file_path = article_file_path_post_date_map['file_path']
        text += __get_index_article_block(os.path.basename(current_file_path), meta_infomation_map=__get_article_mata_infomation(current_file_path.replace('.html', '.txt')), is_index=False) + WRAPPER
    text += '</div">' + WRAPPER

    text += '</article>' + WRAPPER

    return text

def __get_article_mata_infomation(file_path):
    with open(file_path, 'r', encoding='UTF-8') as f:
        content = f.read().split('\n')
    result = {}
    for line in content:
        kv = line.split('\t')
        result[kv[0]] = kv[1]
    return result


def __get_index_article_block(article_file_name, meta_infomation_map, is_index):
    post_date_parts = meta_infomation_map['post_date'].split('-')
    post_date = datetime.date(int(post_date_parts[0]), int(post_date_parts[1]), int(post_date_parts[2]))

    if is_index:
        relative_path_prefix = ''
    else:
        relative_path_prefix = '../'

    image_link = '{}image/index/{}'.format(relative_path_prefix, meta_infomation_map['article_image_filename'])
    article_link = '{}{}/{}'.format(relative_path_prefix, OUTPUT_ARTICLE_DIRECTORY_NAME, article_file_name)

    index_build_result_text = ''
    index_build_result_text += '        <div class="article-block">' + WRAPPER
    index_build_result_text += '            <div class="article-column">' + WRAPPER
    index_build_result_text += '                <a href="{}">'.format(article_link) + WRAPPER
    index_build_result_text += '                    <img class="article-image" src="{}" alt="{}"/>'.format(image_link, os.path.basename(meta_infomation_map['article_image_filename'])) + WRAPPER
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
        index_build_result_text += __write_tag_link(tag, is_index)
    index_build_result_text += '                </ul>' + WRAPPER
    index_build_result_text += '            </div>' + WRAPPER
    index_build_result_text += '        </div>' + WRAPPER
    return index_build_result_text

def __get_tag_en(tag):
    if tag in tag_ens:
        return tag_ens[tag]
    else:
        return tag.lower()
    
def __write_tag_link(tag, is_index):
    tag_en = __get_tag_en(tag)
    if is_index:
        link = '{}/{}'.format(OUTPUT_SEARCH_DIRECTORY_NAME, tag_en + ".html")
    else:
        link = '{}/{}'.format('../' + OUTPUT_SEARCH_DIRECTORY_NAME, tag_en + ".html")
    tag_link_text = ''
    tag_link_text += '        <li class="tag">' + WRAPPER
    tag_link_text += '            <a href="{}">'.format(link) + WRAPPER
    tag_link_text += '                {}'.format(tag) + WRAPPER
    tag_link_text += '            </a>' + WRAPPER
    tag_link_text += '        </li>' + WRAPPER
    return tag_link_text


def __remove_before_run(build_root_path):
    targets = []
    targets += glob.glob(f'{build_root_path}/{OUTPUT_OUTPUT_DIRECTORY_NAME}/{OUTPUT_ARTICLE_DIRECTORY_NAME}/*')
    targets += glob.glob(f'{build_root_path}/{OUTPUT_OUTPUT_DIRECTORY_NAME}/{OUTPUT_SEARCH_DIRECTORY_NAME}/*')
    targets += [f'{build_root_path}/{OUTPUT_OUTPUT_DIRECTORY_NAME}/index.html']
    for target in targets:
        if os.path.exists(target):
            os.remove(target)

def __sitemap_builder(head_infomation_map, article_path_mata_infomation_map):
    blog_root = head_infomation_map['blog_root_url']
    if not blog_root.endswith('/'):
        blog_root += '/'

    text = '<?xml version="1.0" encoding="UTF-8"?>' + WRAPPER
    text += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' + WRAPPER
    text += '<url>' + WRAPPER
    text += '   <loc>{}</loc>'.format(head_infomation_map['blog_root_url']) + WRAPPER
    text += '   <priority>1.0</priority>' + WRAPPER
    text += '</url>' + WRAPPER
    for article_path, mata_infomation_map in article_path_mata_infomation_map.items():
        text += '<url>' + WRAPPER
        text += '   <loc>{}{}/{}</loc>'.format(blog_root, OUTPUT_ARTICLE_DIRECTORY_NAME, os.path.basename(article_path)) + WRAPPER
        text += '   <priority>0.8</priority>' + WRAPPER
        if 'update_date' not in mata_infomation_map and mata_infomation_map['post_date'][:10] != mata_infomation_map['update_date'][:10]:
            text += '    <lastmod>{}</lastmod>'.format(mata_infomation_map['update_date']) + WRAPPER
        text += '</url>' + WRAPPER
        text += '</urlset>' + WRAPPER
    return text


if __name__ == '__main__':
    main()