from ulauncher.api import Extension, Result, effects
import requests

# Icon mapping for parts of speech
PART_OF_SPEECH_ICONS = {
    'noun': '▪',
    'verb': '▸',
    'adjective': '◆',
    'adverb': '◇',
    'pronoun': '●',
    'preposition': '○',
    'conjunction': '◐',
    'interjection': '◉',
    'exclamation': '◎'
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
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()

                if data and len(data) > 0:
                    entry = data[0]
                    phonetic = entry.get('phonetic', '')

                    # Get synonyms if available
                    all_synonyms = []
                    for meaning in entry.get('meanings', []):
                        for defn in meaning.get('definitions', []):
                            all_synonyms.extend(defn.get('synonyms', []))

                    # Process each part of speech
                    for meaning in entry.get('meanings', [])[:3]:
                        part_of_speech = meaning.get('partOfSpeech', '')
                        pos_icon = get_pos_icon(part_of_speech)
                        definitions = meaning.get('definitions', [])

                        # Build description with multiple lines
                        description_lines = []

                        for defn in definitions[:5]:
                            definition_text = defn.get('definition', '')
                            example = defn.get('example', '')
                            synonyms = defn.get('synonyms', [])[:3]

                            line = f"• {definition_text}"
                            if example:
                                line += f"\n  → \"{example}\""
                            if synonyms:
                                line += f"\n  ~ {', '.join(synonyms)}"

                            description_lines.append(line)

                        # Single blank line between definitions
                        description = "\n".join(description_lines)

                        # Build title with icon and synonyms
                        title = f"{pos_icon} <b>{word.title()}</b>"
                        if phonetic:
                            title += f" /{phonetic}/"
                        title += f" · {part_of_speech}\n"

                        # Add top synonyms to title if available
                        top_synonyms = list(set(all_synonyms))[:3]
                        if top_synonyms:
                            title += f" → {', '.join(top_synonyms)}"

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
