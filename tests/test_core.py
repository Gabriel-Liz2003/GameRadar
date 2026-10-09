import json
from pathlib import Path
import tempfile
import unittest
from gameradar.core import normalize, process, money, matches, feed, notify, collect, valid_url

SOURCE={"id":"fixture","name":"Feed autorizado","currency":"BRL"}
ITEM={"id":"game123","title":"Mario Kart 8 Nintendo Switch mídia física usado","price":179.90,
      "url":"https://example.org/oferta/123","condition":"used"}

class GameRadarTests(unittest.TestCase):
    def test_numbers(self):
        self.assertEqual(money("R$ 1.299,90"),1299.9)
        self.assertEqual(money("BRL 175,50"),175.5)
        self.assertEqual(money(159.9),159.9)
        self.assertIsNone(money("sem preço"))

    def test_valid_https(self):
        self.assertTrue(valid_url("https://example.org/item"))
        self.assertFalse(valid_url("http://example.org/item"))
        self.assertFalse(valid_url("https://localhost/test"))
        self.assertFalse(valid_url("https://127.0.0.1/test"))

    def test_classification(self):
        self.assertEqual(normalize(SOURCE,ITEM)["platform"],"switch")
        self.assertEqual(normalize(SOURCE,dict(ITEM,title="Zelda Nintendo Switch 2"))["platform"],"switch2")
        self.assertEqual(normalize(SOURCE,dict(ITEM,title="Mario Switch 2 digital")),None)
        self.assertEqual(normalize(SOURCE,dict(ITEM,title="Controle para Switch")),None)
        self.assertIsNone(normalize(SOURCE,dict(ITEM,url="http://example.org/item")))

    def test_feed(self):
        payload=json.dumps({"items":[ITEM,dict(ITEM,id="skip",title="Jogo digital Nintendo Switch")]}).encode()
        self.assertEqual(len(feed(SOURCE,payload)),1)

    def test_new_after_empty_baseline(self):
        state={"records":{},"initialized_sources":[],"pending":[],"alert_log":[]}
        offer=normalize(SOURCE,ITEM)
        self.assertEqual(process(state,[],["fixture"],{}),[])
        events=process(state,[offer],["fixture"],{})
        self.assertEqual(len(events),1)
        self.assertEqual(events[0]["type"],"new")
        process(state,[offer],["fixture"],{})
        self.assertEqual(len(state["pending"]),1)

    def test_initial_items_not_alerted(self):
        state={"records":{},"initialized_sources":[],"pending":[],"alert_log":[]}
        item=normalize(SOURCE,ITEM)
        self.assertEqual(process(state,[item],["fixture"],{}),[])
        self.assertEqual(state["pending"],[])

    def test_drop(self):
        state={"records":{},"initialized_sources":[],"pending":[],"alert_log":[]}
        item=normalize(SOURCE,ITEM)
        process(state,[item],["fixture"],{})
        cheaper=dict(item,price=130)
        events=process(state,[cheaper],["fixture"],{"min_drop_percent":10,"min_drop_brl":15})
        self.assertEqual(events[0]["type"],"drop")
        process(state,[cheaper],["fixture"],{})
        self.assertEqual(len(state["pending"]),1)

    def test_filter(self):
        item=normalize(SOURCE,ITEM)
        self.assertFalse(matches(item,{"max_price":100}))
        self.assertFalse(matches(item,{"conditions":["new"]}))
        self.assertFalse(matches(item,{"include_keywords":["zelda"]}))
        self.assertTrue(matches(item,{"conditions":["used"]}))

    def test_digest_once(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); (root/"data").mkdir()
            event={"id":"evt","type":"new","offer":normalize(SOURCE,ITEM)}
            (root/"data/state.json").write_text(json.dumps({"pending":[event],"alert_log":[]}))
            sent=[]
            def publisher(items,topic): sent.append((items,topic))
            self.assertEqual(notify(root,"very_long_random_topic_1234",publisher),0)
            self.assertEqual(notify(root,"very_long_random_topic_1234",publisher),0)
            self.assertEqual(len(sent),1)

    def test_notify_failure_keeps_queue(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); (root/"data").mkdir()
            event={"id":"evt","type":"new","offer":normalize(SOURCE,ITEM)}
            (root/"data/state.json").write_text(json.dumps({"pending":[event],"alert_log":[]}))
            def fail(*args): raise RuntimeError("network")
            self.assertEqual(notify(root,"very_long_random_topic_1234",fail),2)
            self.assertEqual(len(json.loads((root/"data/state.json").read_text())["pending"]),1)

    def test_collection_empty(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); (root/"config").mkdir()
            (root/"config/sources.json").write_text(json.dumps({"feeds":[],"mercadolivre_sellers":[]}))
            self.assertEqual(collect(root),0)
            self.assertEqual(json.loads((root/"data/feed.json").read_text())["offers"],[])

if __name__=="__main__": unittest.main()
