<template>
<div>
    <component :is="currentComponent" :selected-load-event = "store.selectedLoadEvent" />
</div>
</template>

<script setup>
import { computed, watch } from 'vue';
import TaskDetailsView from '@/arches_doorstep/etl_modules/ImportSingleCsvWithProcessing/views/TaskDetailsView.vue';
import TaskStatusView from '@/arches_doorstep/etl_modules/ImportSingleCsvWithProcessing/views/TaskStatusView.vue';
import store from './store/mainStore.js';

const state = store.state;

watch(() => state.state, (newValue) => {
    store.setState(newValue);
});

watch(() => state.selectedLoadEvent, (newValue) => {
    store.setSelectedLoadEvent(newValue);
});

const currentComponent = computed(() => {
    console.log(state.state);
    return state.state == 'details' ? TaskDetailsView : TaskStatusView;
});
</script>

<style>
</style>
