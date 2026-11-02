"""Build a user-reviewed GitHub draft URL; no network, tokens or file reads."""
from urllib.parse import urlencode

ISSUES_URL = 'https://github.com/AnthemZhou/Node_Console/issues/new'
MAX_URL_BYTES = 7500


def draft_url(description, version, blender_version, platform, language):
    description = description.strip()
    if not description:
        raise ValueError('Describe the problem first')
    title = '[Bug] ' + ' '.join(description.split())[:80]
    body = (f'### Problem\n\n{description}\n\n### Environment\n\n'
            f'- Node Console: {version}\n- Blender: {blender_version}\n'
            f'- Platform: {platform}\n- Node language: {language}\n')
    # Avoid labels/assignees: reporting users may not have triage permissions.
    url = ISSUES_URL + '?' + urlencode({'title': title, 'body': body})
    if len(url.encode('utf-8')) > MAX_URL_BYTES:
        raise ValueError('Report is too long for a GitHub link; shorten it and add details on GitHub')
    return url
