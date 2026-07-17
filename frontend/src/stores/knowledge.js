import { ref } from 'vue'
import { defineStore } from 'pinia'
import http from '@/js/http/api.js'

export const useKnowledgeStore = defineStore('knowledge', () => {
  const documents = ref([])
  const docCount = ref(0)
  const loading = ref(false)
  const uploading = ref(false)

  async function fetchDocuments() {
    loading.value = true
    try {
      const res = await http.get('/api/kb/documents')
      if (res.data?.success) {
        documents.value = res.data.data
        docCount.value = documents.value.filter(d => d.status === 'completed').length
      }
    } catch (e) {
      console.error('获取文档列表失败', e)
    } finally {
      loading.value = false
    }
  }

  async function uploadDocument(file) {
    uploading.value = true
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await http.post('/api/kb/documents/upload', fd)
      if (res.data?.success) {
        await fetchDocuments()
        return true
      }
    } catch (e) {
      console.error('上传失败', e)
      throw e
    } finally {
      uploading.value = false
    }
  }

  async function deleteDocument(docId) {
    try {
      await http.delete(`/api/kb/documents/${docId}`)
      await fetchDocuments()
    } catch (e) {
      console.error('删除失败', e)
    }
  }

  return { documents, docCount, loading, uploading, fetchDocuments, uploadDocument, deleteDocument }
})
