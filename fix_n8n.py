import json

with open(r'd:\Sources\Python\yambot\n8n\yambot track.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

js_code = """const items = $input.all();
const results = [];

for (const item of items) {
  const data = item.json;
  const site = data.site || 'UNKNOWN';
  const keyword = data.keyword || 'UNKNOWN';
  const changes = data.changes || [];
  
  if (changes.length === 0) continue;
  
  let msg = `<b>Tracking update for "${keyword}" (${site.toUpperCase()})</b>\n\n`;
  
  for (const change of changes) {
    const status = change.status;
    const product = change.item;
    
    const title = product.productName || product.title || 'No Title';
    const url = product.productURL || product.url || '';
    const price = product.price || product.curr_price || 'N/A';
    const image = product.imageURL || product.image_url || product.img_url || product.image || product.thumbnail || (product.thumbnails && product.thumbnails[0]) || '';
    
    let extra = [];
    extra.push(`¥${price}`);
    if (product.bids !== undefined) extra.push(`${product.bids} bids`);
    
    let extraStr = extra.length > 0 ? ` (${extra.join(', ')})` : '';
    
    let statusText = '';
    if (status.type === 'new') {
      statusText = '🆕 [New!!]';
    } else if (status.type === 'modified') {
      statusText = '⚠️ [Update!]';
    }
    
    msg += `${statusText} <a href="${url}">${title}</a>${extraStr}\n`;
    
    if (status.type === 'modified') {
      if (status.changes && status.changes.price) {
        msg += `   💰 Giá: <s>${status.changes.price.old}</s> ➡️ ${status.changes.price.new}\n`;
      }
      if (status.changes && status.changes.status) {
        msg += `   Trạng thái: <s>${status.changes.status.old}</s> ➡️ ${status.changes.status.new}\n`;
      }
    }
    
    if (image) {
      msg += `<a href="${image}">&#8205;</a>\n`;
    }
    msg += `\n`;
  }

  results.push({ json: { telegram_text: msg.trim() } });
}

return results;"""

# Update the 'Format Message' node
nodes = [n for n in data['nodes'] if n['name'] != 'Split by Item']
for n in nodes:
    if n['name'] == 'Format Message':
        n['parameters']['jsCode'] = js_code
data['nodes'] = nodes

# Update connections
data['connections']['Split by Keyword'] = {
    'main': [[{'node': 'Format Message', 'type': 'main', 'index': 0}]]
}
if 'Split by Item' in data['connections']:
    del data['connections']['Split by Item']

with open(r'd:\Sources\Python\yambot\n8n\yambot track.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print("done")
