import os
import re

from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.utils import (
    ExtractorError,
    decode_base_n,
    float_or_none,
    int_or_none,
    mimetype2ext,
    str_or_none,
    traverse_obj,
    unescapeHTML,
    url_or_none,
)


_SHORTCODE_ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'


def _shortcode_to_id(shortcode):
    return str(decode_base_n(shortcode, table=_SHORTCODE_ALPHABET))


class ThreadsIE(InfoExtractor):
    IE_NAME = 'threads'
    IE_DESC = 'Threads posts'
    _VALID_URL = r'https?://(?:www\.)?threads\.(?:net|com)/(?:@(?P<username>[^/?#]+)/post/|t/)(?P<id>[A-Za-z0-9_-]+)'

    _GRAPH_FIELDS = ','.join((
        'id',
        'media_product_type',
        'media_type',
        'media_url',
        'gif_url',
        'permalink',
        'owner',
        'username',
        'text',
        'timestamp',
        'shortcode',
        'thumbnail_url',
        'children{id,media_type,media_url,thumbnail_url,permalink,username,text,timestamp,shortcode}',
        'is_quote_post',
        'quoted_post{id,media_type,media_url,thumbnail_url,permalink,username,text,timestamp,shortcode}',
        'reposted_post{id,media_type,media_url,thumbnail_url,permalink,username,text,timestamp,shortcode}',
        'alt_text',
    ))

    _TESTS = [{
        'url': 'https://www.threads.com/@dream.in.sanity/post/DZLiOyeklke',
        'only_matching': True,
    }, {
        'url': 'https://www.threads.net/t/DZLiOyeklke',
        'only_matching': True,
    }]

    def _access_token(self):
        return (
            self._configuration_arg('access_token', [None])[0]
            or os.environ.get('THREADS_ACCESS_TOKEN'))

    def _extract_graph_post(self, shortcode):
        token = self._access_token()
        if not token:
            return None

        post_id = _shortcode_to_id(shortcode)
        return self._download_json(
            f'https://graph.threads.net/v1.0/{post_id}', shortcode,
            note='Downloading Threads Graph API post data',
            query={
                'fields': self._GRAPH_FIELDS,
                'access_token': token,
            }, fatal=False)

    def _iter_dicts(self, value):
        if isinstance(value, dict):
            yield value
            for child in value.values():
                yield from self._iter_dicts(child)
        elif isinstance(value, list):
            for child in value:
                yield from self._iter_dicts(child)

    def _media_entry_from_api_post(self, post, fallback_id):
        media_url = url_or_none(post.get('media_url') or post.get('gif_url'))
        thumbnail = url_or_none(post.get('thumbnail_url'))
        if not media_url:
            return None

        media_type = str_or_none(post.get('media_type'))
        info = {
            'id': str_or_none(post.get('shortcode') or post.get('id')) or fallback_id,
            'url': media_url,
            'title': str_or_none(post.get('text')) or f'Threads post {fallback_id}',
            'description': str_or_none(post.get('text') or post.get('alt_text')),
            'thumbnail': thumbnail,
            'timestamp': int_or_none(post.get('timestamp')),
            'uploader': str_or_none(post.get('username')),
            'webpage_url': url_or_none(post.get('permalink')),
        }
        if media_type:
            info['format_id'] = media_type.lower()
        return info

    def _extract_from_graph(self, post, shortcode):
        entries = []

        for candidate in (post, *(post.get('children') or []), post.get('quoted_post'), post.get('reposted_post')):
            if isinstance(candidate, dict):
                entry = self._media_entry_from_api_post(candidate, shortcode)
                if entry:
                    entries.append(entry)

        if len(entries) == 1:
            return entries[0]
        if entries:
            return {
                '_type': 'playlist',
                'id': shortcode,
                'title': str_or_none(post.get('text')) or f'Threads post {shortcode}',
                'description': str_or_none(post.get('text')),
                'uploader': str_or_none(post.get('username')),
                'entries': entries,
            }
        return None

    def _extract_media_object(self, media, media_id):
        user = media.get('user') or {}
        description = traverse_obj(media, ('caption', 'text'), expected_type=str_or_none)
        thumbnails = [{
            'url': url_or_none(candidate.get('url')),
            'width': int_or_none(candidate.get('width')),
            'height': int_or_none(candidate.get('height')),
        } for candidate in traverse_obj(media, ('image_versions2', 'candidates')) or []]
        thumbnails = [thumbnail for thumbnail in thumbnails if thumbnail.get('url')]

        formats = []
        for fmt in media.get('video_versions') or []:
            if not isinstance(fmt, dict):
                continue
            fmt_url = url_or_none(fmt.get('url'))
            if not fmt_url:
                continue
            formats.append({
                'format_id': str_or_none(fmt.get('id') or fmt.get('type')),
                'url': fmt_url,
                'width': int_or_none(fmt.get('width')),
                'height': int_or_none(fmt.get('height')),
                'vcodec': media.get('video_codec'),
            })

        for key in ('video_url', 'playable_url', 'media_url', 'gif_url'):
            fmt_url = url_or_none(media.get(key))
            if fmt_url and not any(fmt['url'] == fmt_url for fmt in formats):
                formats.append({'url': fmt_url})

        info = {
            'id': str_or_none(media.get('code') or media.get('pk') or media.get('id')) or media_id,
            'title': description or f'Threads post {media_id}',
            'description': description,
            'duration': float_or_none(media.get('video_duration') or media.get('duration')),
            'timestamp': int_or_none(media.get('taken_at') or media.get('taken_at_timestamp')),
            'uploader': str_or_none(user.get('username')),
            'uploader_id': str_or_none(user.get('pk') or user.get('id')),
            'thumbnails': thumbnails,
            'view_count': int_or_none(media.get('view_count')),
            'like_count': int_or_none(media.get('like_count')),
            'comment_count': int_or_none(media.get('comment_count')),
        }

        if formats:
            return {
                **info,
                'formats': formats,
                'http_headers': {'Referer': 'https://www.threads.net/'},
            }

        if thumbnails:
            image = max(thumbnails, key=lambda thumbnail: (
                (thumbnail.get('width') or 0) * (thumbnail.get('height') or 0),
                thumbnail.get('width') or 0,
                thumbnail.get('height') or 0))
            return {
                **info,
                'url': image['url'],
                'width': image.get('width'),
                'height': image.get('height'),
                'http_headers': {'Referer': 'https://www.threads.net/'},
            }

        return None

    def _extract_public_media(self, webpage, shortcode):
        target_id = _shortcode_to_id(shortcode)
        target_media = []
        target_seen = set()
        fallback_entries = []
        fallback_seen = set()

        def add_fallback_url(media_url, media=None):
            media_url = url_or_none(media_url)
            if not media_url or media_url in fallback_seen:
                return
            fallback_seen.add(media_url)
            media = media or {}
            ext = mimetype2ext(media.get('mime_type')) or None
            fallback_entries.append({
                'id': f'{shortcode}-{len(fallback_entries) + 1}',
                'url': media_url,
                'title': f'Threads post {shortcode}',
                'ext': ext,
                'width': int_or_none(media.get('width')),
                'height': int_or_none(media.get('height')),
                'duration': int_or_none(media.get('duration')),
                'thumbnail': traverse_obj(media, (
                    ('thumbnail_url', 'display_url'),
                    {url_or_none}, any)),
            })

        def collect_target_media(obj):
            for item in self._iter_dicts(obj):
                item_id = str_or_none(item.get('pk') or item.get('id'))
                if (
                        item.get('code') == shortcode
                        or item_id == target_id
                        or (item_id and item_id.startswith(f'{target_id}_'))):
                    target_key = item.get('code') or item_id
                    if target_key and target_key not in target_seen:
                        target_seen.add(target_key)
                        target_media.append(item)

        for media_url in re.findall(r'https?:\\?/\\?/[^"\'<>\\\s]+?\.(?:mp4|m3u8)(?:\?[^"\'<>\\\s]+)?', webpage):
            add_fallback_url(media_url.replace('\\/', '/'))

        for obj in self._yield_json_ld(webpage, shortcode, fatal=False) or []:
            collect_target_media(obj)

        for mobj in re.finditer(
                r'<script[^>]+type=["\']application/json["\'][^>]*>(?P<json>.*?)</script>',
                webpage, flags=re.DOTALL):
            script_json = self._parse_json(unescapeHTML(mobj.group('json')), shortcode, fatal=False)
            if script_json:
                collect_target_media(script_json)

        entries = []
        for media in target_media:
            carousel_media = media.get('carousel_media')
            if carousel_media:
                for idx, child_media in enumerate(carousel_media, start=1):
                    entry = self._extract_media_object(child_media, f'{shortcode}-{idx}')
                    if entry:
                        entries.append(entry)
                continue
            entry = self._extract_media_object(media, shortcode)
            if entry:
                entries.append(entry)

        if not entries:
            entries = fallback_entries

        if not entries:
            return None

        if len(entries) == 1:
            return entries[0]
        return {
            '_type': 'playlist',
            'id': shortcode,
            'title': f'Threads post {shortcode}',
            'entries': entries,
        }

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        shortcode = mobj.group('id')
        username = mobj.group('username')

        graph_post = self._extract_graph_post(shortcode)
        if graph_post:
            graph_result = self._extract_from_graph(graph_post, shortcode)
            if graph_result:
                return graph_result

        webpage = self._download_webpage(
            url, shortcode, fatal=False, headers={
                'User-Agent': self.get_param('http_headers', {}).get(
                    'User-Agent',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/125 Safari/537.36'),
            })
        if webpage:
            public_result = self._extract_public_media(webpage, shortcode)
            if public_result:
                public_result.setdefault('uploader', username)
                return public_result

        raise ExtractorError(
            'Unable to find downloadable Threads media in the public page. '
            'If this post is public but the page shell omits media data, pass a Threads Graph API '
            'token with --extractor-args "threads:access_token=TOKEN" or THREADS_ACCESS_TOKEN.',
            expected=True)
