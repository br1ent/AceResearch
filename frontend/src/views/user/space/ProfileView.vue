<script setup>
import AvatarCard from './compoenents/AvatarCard.vue'
import ProfileCard from './compoenents/ProfileCard.vue'
import ApiKeyCard from './compoenents/ApiKeyCard.vue'
</script>

<template>
  <main class="max-w-4xl mx-auto px-5 py-10">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">

      <!-- 左侧：头像 -->
      <div class="md:col-span-1">
        <div class="card bg-base-100 shadow-xl">
          <div class="card-body items-center py-8">
            <AvatarCard />
          </div>
        </div>
      </div>

      <!-- 右侧：资料 + API Key 配置 -->
      <div class="md:col-span-2 flex flex-col gap-6">
        <div class="card bg-base-100 shadow-xl">
          <div class="card-body">
            <ProfileCard />
          </div>
        </div>
        <div class="card bg-base-100 shadow-xl">
          <div class="card-body">
            <ApiKeyCard />
          </div>
        </div>
      </div>

    </div>
  </main>
</template>
