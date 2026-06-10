# yt-dlp Threads extractor plugin

Standalone `yt-dlp` extractor plugin for Threads post URLs.

## Usage

From this directory's parent:

```powershell
yt-dlp --plugin-dirs .\threads-ytdlp-extractor\plugins "https://www.threads.com/@dream.in.sanity/post/DZLiOyeklke"
```

To use Meta's Threads Graph API when you have an access token:

```powershell
yt-dlp --plugin-dirs .\threads-ytdlp-extractor\plugins --extractor-args "threads:access_token=TOKEN" "https://www.threads.net/@username/post/SHORTCODE"
```

or:

```powershell
$env:THREADS_ACCESS_TOKEN = "TOKEN"
yt-dlp --plugin-dirs .\threads-ytdlp-extractor\plugins "https://www.threads.net/@username/post/SHORTCODE"
```

## Notes

Threads does not consistently expose post media in unauthenticated HTML. The extractor first tries public page data and direct media references. If that does not expose downloadable media, it uses the official Threads Graph API path when an access token is provided.

The Graph API accepts numeric thread IDs, while public URLs use shortcodes. This plugin converts shortcodes to numeric IDs using the same base64url alphabet used by Instagram/Threads media IDs.
