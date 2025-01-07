<script setup>
import { defineProps, watch } from 'vue';
import Table from '../../../components/Table.vue';
const props = defineProps({
    dateRows: Array,
    dateHeaders: Array
})
</script>

<template>
    <div>
        <Table 
            title = "Dates"
            :headers ="dateHeaders"
            :rows ="dateRows"
        />          
    </div>
</template>

<style scoped>
.summary-tables {
    max-height: 250px;
    margin-bottom: 4rem;
}
</style>