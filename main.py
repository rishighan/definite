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
    def on_event(self, event, extension):
        query = event.get_argument() or ""
        
        if not query.strip():
            return RenderResultListAction([
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='Type a word to define',
                    description='Enter a word to look up its definition',
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
                    
                    # Process each part of speech
                    for meaning in entry.get('meanings', [])[:3]:
                        part_of_speech = meaning.get('partOfSpeech', '').upper()
                        definitions = meaning.get('definitions', [])
                        
                        # Build description with multiple lines
                        description_lines = []
                        
                        for idx, defn in enumerate(definitions[:5], 1):
                            definition_text = defn.get('definition', '')
                            example = defn.get('example', '')
                            
                            line = f"{idx}. {definition_text}"
                            if example:
                                line += f"\n   → \"{example}\""
                            
                            description_lines.append(line)
                        
                        description = "\n".join(description_lines)
                        
                        # Build title
                        title = f"{word.title()}"
                        if phonetic:
                            title += f" {phonetic}"
                        title += f" • {part_of_speech}"
                        
                        items.append(ExtensionResultItem(
                            icon='images/icon.png',
                            name=title,
                            description=description,
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