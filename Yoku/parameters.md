# Yahoo! Auctions URL Parameters Guide (Unofficial)

## Base URL

https://auctions.yahoo.co.jp/search/search

## `p`
The search keyword. (p for parameter?)

Value: URL-encoded string

Note: Overrides `va`, `vo` and `ve`. Using `p` automatically invalidates `va`, `vo` and `ve`.

## `va`, `vo`, `ve`
Advanced search options for keywords. Items that contain all of the keywords in `va`, at least one of the keywords in `vo` and none of the keywords in `ve` are shown.

"Keywords" in these parameters are separated by spaces (which, after URL encoding, becomes +).

Value: URL-encoded strings

Notes:
- Using `va` alone is equivalent to using `p`.
- `ve` cannot be used alone without `va` or `vo`.
- Overrided by `p`. Using `p` automatically invalidates `va`, `vo` and `ve`.

## `auccat`
Auction category (set with カテゴリ).

Value: positive integer

Example:

`auccat=22152`: 音楽

## `brand_id`
Brand ID (set with メーカー・ブランド).

Value: positive integer

Example:

`brand_id=101091`: SONY

## `aucmaxprice`
Auction max price (set with 価格). If set, only auctions whose current price is below this parameter are shown.

Value: positive integer

Note:
- only a few options are provided in the 価格 section, but the parameter works for any positive integer.
- Overrides `min` and `max`. Using `aucmaxprice` automatically invalidates `min` and `max`.

## `min`, `max`, `price_type`

Price ranges in detail (set with 価格指定).

Value:

`min`, `max`: positive integers

`price_type`: {currentprice,bidorbuyprice}

Specifically,
- `price_type=currentprice`: 現在価格
- `price_type=bidorbuyprice`: 即決価格

Note:
- `min` and `max` cannot be used alone without `price_type`.
- Overrided by `aucmaxprice`. Using `aucmaxprice` automatically invalidates `min` and `max`.

## `b`, `n`
Begin position (set with selecting pages) and number of items per page (set with 20/50/100件表示).

Value:

`b`: positive integer

`n`: {20,50,100}

## `s1`, `o1`
Sorting method and order (set with おすすめ順/...).

Value:

`s1`: {score2,new,end,tbids,tbidorbuy,bids,popular,featured}

`o1`: {a,d} (ascending / descending)

Specifically,
- `s1=score2&o1=d`: おすすめ順
- `s1=new&o1=d`: 新着順
- `s1=end&o1=a`: 残り時間の短い順
- `s1=end&o1=d`: 残り時間の長い順
- `s1=tbids&o1=a`: 現在価格の安い順（送料込み）
- `s1=tbids&o1=d`: 現在価格の高い順（送料込み）
- `s1=tbidorbuy&o1=a`: 即決価格の安い順（送料込み）
- `s1=tbidorbuy&o1=d`: 即決価格の高い順（送料込み）
- `s1=bids&o1=a`: 入札件数の多い順
- `s1=bids&o1=d`: 入札件数の少ない順
- `s1=popular&o1=d`: 人気順
- `s1=featured&o1=d`: 注目のオークション順

Other combinations do not have a name but may work.

## `fixed`
Whether the price is fixed (set by selecting tabs).

Value:

{1,2,3}

Specifically,
- `fixed=1`: 定額（即決）
- `fixed=2`: オークション
- `fixed=3`: すべて

## `istatus`
Item status (set with 商品の状態).

Value:

{1,2,3,4,5,6,7}

Specifically,
- `istatus=1`: 未使用
- `istatus=2`: 中古
- `istatus=3`: 未使用に近い
- `istatus=4`: 目立った傷や汚れなし
- `istatus=5`: やや傷や汚れあり
- `istatus=6`: 傷や汚れあり
- `istatus=7`: 全体的に状態が悪い

Note: multiple choice, seperate values with comma (which, after URL encoding, becomes %2C).

Example:

`istatus=3%2C4%2C6`: 未使用に近い or 目立った傷や汚れなし or 傷や汚れあり

Note: `istatus=3%2C4%2C5%2C6%2C7` is equivalent to `istatus=2`

## `is_postage_mode`, `dest_pref_code`
If the postage is shown below the prices (set with 送料を表示), and destination preference code, used to calculate postages (set with ...を設定中).

Value:
`is_postage_mode`: {0,1} (no / yes)

`dest_pref_code`: integer between 1 and 48. 1 to 47 each corresponds to a Japanese prefecture, 48 is abroad.

Example: 

`is_postage_mode=1&dest_pref_code=13`: 東京都を設定中

## Others

I have also encountered these parameters while using, but haven't figured out their exact meanings and values.

```
tab_ex={commerce}
ei={utf-8} // encoding
aq={-1}
oq=
sc_i=
fr={auc_top} // from?
x={0} // some kind of coordinates
y={0}
exflg={1} // extra flag?
rc_ng={1}
```

Also the ＋条件指定 page may utilize other parameters for advanced search.


## References

https://github.com/richardmin/YahooAuctionScraper/blob/master/src/scraper/search_result.py

https://github.com/kokseen1/Yoku/blob/main/yoku/scrape.py

