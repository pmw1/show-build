<template>
  <Transition name="banner-slide">
    <div v-if="visible" class="join-preview-banner">
      <div class="banner-content">
        <div class="banner-left">
          <v-icon color="white" size="large" class="mr-3">mdi-set-merge</v-icon>
          <div>
            <div class="banner-title">Join Preview</div>
            <div class="banner-subtitle">Changes to the rundown or script are not allowed until the join is either accepted or rejected.</div>
          </div>
        </div>
        <div class="banner-center">
          <span class="banner-restore-info" v-if="snapshotName">
            Restore point: <strong>{{ snapshotName }}</strong>
          </span>
        </div>
        <div class="banner-right">
          <v-btn
            color="error"
            variant="elevated"
            @click="$emit('reject')"
            class="mr-4 banner-btn"
          >
            <v-icon class="mr-1">mdi-close-circle</v-icon>
            Reject
          </v-btn>
          <v-btn
            color="success"
            variant="elevated"
            @click="$emit('accept')"
            class="banner-btn"
          >
            <v-icon class="mr-1">mdi-check-circle</v-icon>
            Accept Join
          </v-btn>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: false },
  snapshotName: { type: String, default: '' }
})

defineEmits(['accept', 'reject'])
</script>

<style scoped>
.join-preview-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 110px;
  z-index: 9999;
  background: linear-gradient(135deg, #1a237e 0%, #311b92 50%, #4a148c 100%);
  box-shadow: 0 6px 30px rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 3px solid rgba(206, 147, 216, 0.4);
}

.banner-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  max-width: 100%;
  padding: 0 32px;
  color: white;
}

.banner-left {
  display: flex;
  align-items: center;
  gap: 4px;
}

.banner-title {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.banner-subtitle {
  font-size: 12px;
  opacity: 0.6;
  margin-top: 2px;
}

.banner-center {
  display: flex;
  align-items: center;
}

.banner-restore-info {
  font-size: 11px;
  opacity: 0.5;
  background: rgba(255, 255, 255, 0.08);
  padding: 6px 16px;
  border-radius: 4px;
}

.banner-right {
  display: flex;
  align-items: center;
}

.banner-btn {
  min-width: 120px;
  height: 40px;
  font-weight: 600;
  letter-spacing: 0.3px;
}

/* Transition */
.banner-slide-enter-active,
.banner-slide-leave-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}
.banner-slide-enter-from,
.banner-slide-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}
</style>
