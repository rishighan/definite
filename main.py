from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
import requests

class DefiniteExtension(Extension):
    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())

class KeywordQueryEventListener(EventListener):
    
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
    
    def get_pos_icon(self, pos):
        """Get icon for part of speech"""
        return self.PART_OF_SPEECH_ICONS.get(pos.lower(), '■')
    
    def on_event(self, event, extension):
        query = event.get_argument() or ""
        
        if not query.strip():
            return RenderResultListAction([
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='Type a word to define',
                    description='Enter any word to discover its meaning, usage, and examples',
                    on_enter=HideWindowAction()
                )
            ])
        
        word = query.strip()
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
                        pos_icon = self.get_pos_icon(part_of_speech)
                        definitions = meaning.get('definitions', [])
                        
                        # Build description with multiple lines
                        description_lines = []
                        
                        for idx, defn in enumerate(definitions[:5], 1):
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
                        
                        items.append(ExtensionResultItem(
                            icon='images/icon.png',
                            name=title,
                            description=description + "\n",
                            on_enter=CopyToClipboardAction(description)
                        ))
            else:
                items.append(ExtensionResultItem(
                    icon='images/icon.png',
                    name=f'No definition found for "{word}"',
                    description='Try checking the spelling or use a different word',
                    on_enter=HideWindowAction()
                ))
                
        except requests.exceptions.RequestException as e:
            items.append(ExtensionResultItem(
                icon='images/icon.png',
                name='Connection error',
                description='Could not reach dictionary API. Check your internet connection.',
                on_enter=HideWindowAction()
            ))
        except Exception as e:
            items.append(ExtensionResultItem(
                icon='images/icon.png',
                name='Error occurred',
                description=str(e),
                on_enter=HideWindowAction()
            ))
        
        return RenderResultListAction(items)

if __name__ == '__main__':
    DefiniteExtension().run()