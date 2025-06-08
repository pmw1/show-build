<!-- RundownManager.vue -->
<template>
  <div>
    <h2>Episode Rundown</h2>

    <draggable :list="segments" item-key="getItemKey">
      <template #item="{ element, index }">
        <div
          :key="getItemKey(element)"
          style="border: 1px solid black; padding: 8px; margin: 4px; background-color: #f9f9f9;"
        >
          <strong>{{ index + 1 }}. {{ element.title || 'Untitled' }}</strong><br />
          Slug: {{ element.slug || element.filename }}<br />
          Duration: {{ element.duration || '—' }}<br />
          Type: {{ element.item_type || '—' }}<br />
          Asset ID: {{ element.asset_id || '—' }}<br />
        </div>
      </template>
    </draggable>

    <button @click="saveOrder" style="margin-top: 16px;">Save Order</button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import draggable from 'vuedraggable'
import axios from 'axios'

const segments = ref([])

const getItemKey = (item) => item.slug || item.filename || item.title || Math.random().toString(36)

onMounted(async () => {
  try {
    const response = await axios.get('http://192.168.51.210:8888/rundown/0225')
    segments.value = response.data
    console.log("Fetched segments:", segments.value)
  } catch (error) {
    console.error("Failed to fetch rundown:", error)
  }
})

const saveOrder = async () => {
  try {
    const payload = segments.value.map(segment => ({ filename: segment.filename }))
    const response = await axios.post('http://192.168.51.210:8888/rundown/0225/reorder', payload)
    console.log("Save response:", response.data)
    alert("Order saved successfully!")
  } catch (error) {
    console.error("Failed to save order:", error)
    alert("Failed to save order.")
  }
}
</script>

