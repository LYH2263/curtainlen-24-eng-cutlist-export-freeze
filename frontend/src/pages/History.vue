<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'
const items = ref([])
const exported = ref(null)
const err = ref('')
async function load() { items.value = (await getJSON('/api/runs')).items }
async function exportCutSheet() {
  err.value = ''
  try { exported.value = await postJSON('/api/exports/cut-sheet', {}) }
  catch (e) { err.value = String(e) }
}
onMounted(load)
</script>
<template>
  <div class="page">
    <h1>记录</h1>
    <button @click="exportCutSheet">导出裁幅清单（冻结首条）</button>
    <p v-if="exported">已冻结 run #{{ exported.run_id }}：{{ exported.panels }} 幅 / {{ exported.meters }}m，checksum {{ exported.content_checksum }}</p>
    <p v-if="err">{{ err }}</p>
    <ul><li v-for="r in items" :key="r.id">{{ r.window_name }} {{ r.result?.meters }}m</li></ul>
  </div>
</template>
