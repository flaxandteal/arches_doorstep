<script setup>
import { defineProps } from 'vue';

const props = defineProps({
    dateRows: Array,
    dateHeaders: Array
})
</script>

<template>
    <div>
        <DataTable :value="dateRows" scrollable scroll-height="250px" class="csv-mapping-table-container summary-tables">
            <Column 
                v-for="header in dateHeaders" 
                :key="header" :field="header" 
                :header="header" 
            />
        </DataTable>                 
    </div>
</template>

<style scoped>

</style>