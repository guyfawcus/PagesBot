### About

Wikidata bot that adds 'number of pages' (P1104) statements to items

See [PagesBot on Wikidata](https://www.wikidata.org/wiki/User:PagesBot)

### Use

- Use pip to install wikibaseintegrator v0.12+
- Add your credentials to the top of the script
- Then with your own Python script in the same directory:

```python
import pagesbot
sandbox_qid = 'Q4115189'
pagesbot.parse_item(sandbox_qid, write_changes=False)
```
