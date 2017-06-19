# torequests  - v4.0.0

## Inspired by [tomorrow](https://github.com/madisonmay/Tomorrow). To make async-coding EASY & smooth, nothing to learn.(It fits Windows, Python 2/3 compatible) -- Rookie fast asyncio assistant

## Give one way to use async functions easily & make asynchronous requests.




# USAGE / DOC / TEST / DEMO TO BE DONE

> mock server

```python
from gevent.monkey import patch_all
patch_all()
import bottle

app = bottle.Bottle()

@app.get('/test/<num>')
def test(num):
    return 'ok %s' % num

app.run(server='gevent', port=5000)
```

