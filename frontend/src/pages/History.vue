<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'
const items = ref([])
const frozen = ref(null)
const err = ref('')
onMounted(async () => { items.value = (await getJSON('/api/runs')).items })
async function freeze() {
  err.value = ''
  try { frozen.value = await postJSON('/api/exports/cut-sheet', {}) }
  catch (e) { err.value = String(e) }
}
</script>
<template><div class="page"><h1>记录</h1>
<button @click="freeze">导出裁幅清单（冻结）</button>
<p v-if="frozen">已冻结 run#{{ frozen.run_id }}：{{ frozen.panels }}幅 {{ frozen.meters }}m · {{ frozen.lines }}行 · {{ frozen.content_checksum }}</p>
<p v-if="err">{{ err }}</p>
<ul><li v-for="r in items" :key="r.id">{{ r.window_name }} {{ r.result?.meters }}m</li></ul>
</div></template>
