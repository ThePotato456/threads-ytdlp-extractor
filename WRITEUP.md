# Threads yt-dlp Extractor Writeup

## Starting Point

The initial test used the installed `yt-dlp` directly against:

```powershell
yt-dlp "https://www.threads.com/@dream.in.sanity/post/DZLiOyeklke"
```

The first run was blocked by sandboxed network permissions. After rerunning with network access, `yt-dlp` fell back to the generic extractor and failed with:

```text
ERROR: Unsupported URL: https://www.threads.com/@dream.in.sanity/post/DZLiOyeklke
```

Checking the installed extractor list showed Facebook and Instagram support, but no Threads extractor. That meant the fix needed to be a new `yt-dlp` extractor rather than a configuration change.

## Project Shape

The extractor was built as a standalone `yt-dlp` plugin under:

```text
threads-ytdlp-extractor/
  plugins/
    threads/
      yt_dlp_plugins/
        extractor/
          threads.py
  tests/
    test_threads.py
  README.md
  WRITEUP.md
```

`yt-dlp` plugins are loaded from directories passed with `--plugin-dirs`. For extractor plugins, the important package path is:

```text
yt_dlp_plugins/extractor/*.py
```

Any public class ending in `IE` is discovered as an extractor. This project defines `ThreadsIE`.

## URL Matching

The extractor supports both current public Threads hostnames:

```text
threads.com
threads.net
```

It matches post URLs like:

```text
https://www.threads.com/@username/post/SHORTCODE
https://www.threads.net/@username/post/SHORTCODE
https://www.threads.net/t/SHORTCODE
```

The URL shortcode is captured as the media ID used by `yt-dlp`.

## Shortcode Conversion

Threads public URLs use a shortcode, while the page data and Graph API use a numeric media/post ID.

The extractor converts the shortcode using the same base64url alphabet used by Instagram-style media IDs:

```python
ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_
```

For the tested post:

```text
DZLiOyeklke -> 3912371251155458334
```

That numeric ID appears in the Threads page's Relay preload data as the target `postID`.

## Extraction Strategy

The extractor has two paths.

### 1. Optional Graph API Path

If a token is available, the extractor can call:

```text
https://graph.threads.net/v1.0/{numeric_post_id}
```

The token can be provided as either:

```powershell
$env:THREADS_ACCESS_TOKEN = "TOKEN"
```

or:

```powershell
yt-dlp --extractor-args "threads:access_token=TOKEN" ...
```

This path is useful when public HTML does not expose usable media data.

### 2. Public Page Scraping Path

For the tested post, authenticated API access was not needed.

The extractor downloads the public Threads page and walks the embedded JSON script payloads. Threads uses Relay preload data, and the target post appears inside that payload with fields such as:

```text
pk
code
caption
user
image_versions2
video_versions
video_duration
```

The extractor only accepts media objects whose:

```text
code == requested shortcode
```

or whose:

```text
pk/id == converted numeric post ID
```

This prevents related posts, profile pictures, thumbnails, and recommendation media from being treated as download targets.

For video posts, `video_versions` are converted into yt-dlp formats. Thumbnail candidates come from `image_versions2`.

For image-only posts, the largest image candidate is returned as the downloadable URL.

## Verification

The plugin was smoke-tested with the installed `yt-dlp.exe`:

```powershell
yt-dlp --plugin-dirs .\threads-ytdlp-extractor\plugins --simulate --print "%(extractor)s %(id)s %(ext)s" "https://www.threads.com/@dream.in.sanity/post/DZLiOyeklke"
```

The result was:

```text
threads DZLiOyeklke mp4
```

A real download was then run:

```powershell
yt-dlp --plugin-dirs .\threads-ytdlp-extractor\plugins -o "threads-ytdlp-extractor\downloads\%(id)s.%(ext)s" "https://www.threads.com/@dream.in.sanity/post/DZLiOyeklke"
```

That successfully wrote:

```text
threads-ytdlp-extractor/downloads/DZLiOyeklke.mp4
```

The downloaded file was about 17.26 MiB.

## Upload

After the extractor worked and the file downloaded successfully, the resulting MP4 was uploaded with:

```powershell
scp .\threads-ytdlp-extractor\downloads\DZLiOyeklke.mp4 user@arch-server.local:/srv/tempfiles/uploads/
```

The upload completed successfully.

## Current Limitations

Threads is not a stable scrape target. Public pages may change shape, may omit media data, or may expose different Relay payloads depending on host, headers, region, login state, or post visibility.

The plugin handles the tested public post and similar public post payloads. If Threads stops embedding post media in public HTML, the intended fallback is the Graph API token path.
