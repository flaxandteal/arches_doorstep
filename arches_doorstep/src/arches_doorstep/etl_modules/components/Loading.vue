<script setup>
import ProgressSpinner from 'primevue/progressspinner';
</script>

<template>
    <div class="loading-overlay">
        <ProgressSpinner />
    </div>
</template>

<style scoped>
.loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    bottom: 0;
    width: 100%;
    height: 100%;
    background: rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(5px);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 9999;
}
</style>