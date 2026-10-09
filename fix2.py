import re
with open('static/js/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

js = js.replace("propSizeSqm.value = data.property.size_sqm ?? propSizeSqm.value;", "propSizeSqm.value = data.property.size_sqm ?? '';")
js = js.replace("propRooms.value = (data.property.room_count ?? propRooms.value).toFixed(1);", "propRooms.value = data.property.room_count ? data.property.room_count.toFixed(1) : '';")

with open('static/js/app.js', 'w', encoding='utf-8') as f:
    f.write(js)
