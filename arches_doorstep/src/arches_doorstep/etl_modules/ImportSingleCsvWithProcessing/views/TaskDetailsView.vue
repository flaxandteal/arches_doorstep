<template>
    <Tabs class="tab-layout" :value="state.detailsTab">
        <TabList class="custom-tab-list">
            <Tab v-for="tab in tabs" :key="tab.label" class="custom-tab" :value="tab.route">
                <a class="flex items-center margin-2">
                    <i :class="tab.icon" />
                    <span>{{ tab.label }}</span>
                </a>
            </Tab>
        </TabList>
        <TabPanels>
            <TabPanel v-for="tab in tabs" :key="tab.component" :value="tab.route">
                <Loading v-if="state.isLoading"/>
                <component :is="tab.component" />
            </TabPanel>
        </TabPanels>
    </Tabs>
</template>

<script setup>
import { shallowRef } from 'vue';
import Tabs from 'primevue/tabs';
import TabList from 'primevue/tablist';
import Tab from 'primevue/tab';
import TabPanels from 'primevue/tabpanels';
import TabPanel from 'primevue/tabpanel';
import UploadView from './UploadView.vue'
import ProcessingView from './ProcessingView.vue';
import ErrorPreviewView from './ErrorPreviewView.vue';
import Loading from '../../components/Loading.vue';
import store from '../store/mainStore.js';

const tabs = shallowRef([
    { label: 'Upload', route: 'upload', icon: 'fa fa-upload', component: UploadView },
    { label: 'Processing', route: 'process', icon: 'fa fa-cogs', component: ProcessingView },
    { label: 'Error Check', route: 'errors', icon: 'fa fa-exclamation-triangle', component: ErrorPreviewView },
]);

const state = store.state;
</script>

<style scoped>
    .flex{
        display: flex;
    }
    .items-center{
        justify-content: center;
        align-items: center;
    }
    span{
        margin: 0.75rem;
    }
    .tab-layout {
        width: 100%;
        --p-tabs-tab-active-border-color: #2986b8;
        --p-tabs-tab-active-background-color: #2986b8; 
        --p-tabs-tablist-background: #e8e8e8;
        --p-tabs-tab-active-background: #ffffff;
    }
    .custom-tab {
        flex: 1;
        text-align: center;
    }
    ::v-deep(.p-tablist-active-bar){         
        background: #2986b8;
        border-color: #2986b8;
        height: 2px;
    }

    ::v-deep(.p-tabpanels){
        position: relative;
    }

</style>