from ulauncher.api import Extension, Result, effects
import requests

# Icon mapping for parts of speech
PART_OF_SPEECH_ICONS = {
    'n': '▪',
    'v': '▸',
    'adj': '◆',
    'adv': '◇',
    'u': '■'
}

PART_OF_SPEECH_NAMES = {
    'n': 'noun',
    'v': 'verb',
    'adj': 'adjective',
    'adv': 'adverb',
    'u': 'other'
}


def get_pos_icon(pos):
    """Get icon for part of speech"""
    return PART_OF_SPEECH_ICONS.get(pos.lower(), '■')


class DefiniteExtension(Extension):
    def on_input(self, query_str, trigger_id):
        query = (query_str or "").strip()

        if not query:
            return [
                Result(
                    icon='images/icon.png',
                    name='Type a word to define',
                    description='Enter any word to discover its meaning, usage, and examples',
                    actions={"dismiss": {"name": "Close"}}
                )
            ]

        word = query
        items = []

        try:
            url = "https://api.datamuse.com/words"
            response = requests.get(
                url, params={"sp": word, "md": "d", "max": 1}, timeout=5
            )

            if response.status_code == 200:
                data = response.json()

                if data and data[0].get('defs'):
                    entry = data[0]

                    # Group definitions by part of speech, preserving order
                    by_pos = {}
                    for raw in entry['defs']:
                        pos, _, definition_text = raw.partition('\t')
                        by_pos.setdefault(pos, []).append(definition_text.strip())

                    # Fetch a few synonyms for the title
                    synonyms = []
                    try:
                        syn_resp = requests.get(
                            url, params={"rel_syn": word, "max": 3}, timeout=5
                        )
                        if syn_resp.status_code == 200:
                            synonyms = [s['word'] for s in syn_resp.json()]
                    except requests.exceptions.RequestException:
                        pass

                    for pos, definitions in list(by_pos.items())[:3]:
                        pos_icon = get_pos_icon(pos)
                        part_of_speech = PART_OF_SPEECH_NAMES.get(pos.lower(), pos)

                        description_lines = [
                            f"• {definition_text}" for definition_text in definitions[:5]
                        ]
                        description = "\n".join(description_lines)

                        title = f"{pos_icon} {word.title()} · {part_of_speech}\n"
                        if synonyms:
                            title += f" → {', '.join(synonyms)}"

                        items.append(Result(
                            icon='images/icon.png',
                            name=title,
                            description=description + "\n",
                            actions={"copy": {"name": "Copy definition"}}
                        ))
                else:
                    items.append(Result(
                        icon='images/icon.png',
                        name=f'No definition found for "{word}"',
                        description='Try checking the spelling or use a different word',
                        actions={"dismiss": {"name": "Close"}}
                    ))
            else:
                items.append(Result(
                    icon='images/icon.png',
                    name=f'No definition found for "{word}"',
                    description='Try checking the spelling or use a different word',
                    actions={"dismiss": {"name": "Close"}}
                ))

        except requests.exceptions.RequestException:
            items.append(Result(
                icon='images/icon.png',
                name='Connection error',
                description='Could not reach dictionary API. Check your internet connection.',
                actions={"dismiss": {"name": "Close"}}
            ))
        except Exception as e:
            items.append(Result(
                icon='images/icon.png',
                name='Error occurred',
                description=str(e),
                actions={"dismiss": {"name": "Close"}}
            ))

        return items

    def on_result_activation(self, action_id, result):
        if action_id == "copy":
            self.clipboard_store(result.description)
        return effects.close_window()


if __name__ == '__main__':
    DefiniteExtension().run()
