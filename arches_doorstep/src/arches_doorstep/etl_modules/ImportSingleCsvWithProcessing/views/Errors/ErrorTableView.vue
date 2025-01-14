<script setup>
import { defineProps, computed } from 'vue';
import Accordion from 'primevue/accordion';
import AccordionPanel from 'primevue/accordionpanel';
import AccordionHeader from 'primevue/accordionheader';
import AccordionContent from 'primevue/accordioncontent';
import Table from '../../components/Table.vue';

const props = defineProps({
    showSuccess: Boolean,
    successRows: Array,
    warningRows: Array,
    errorRows: Array,
    headers: Array
})

const successRows = computed(() => {
    return props.showSuccess ? props.successRows : [];
})

</script>
<template>
    <div>
        <Accordion multiple>
            <AccordionPanel v-if="props.showSuccess" value="0">
                <AccordionHeader>
                    <div class="header-container">
                        <div>Success</div>
                        <div>{{ successRows.length }}</div>
                    </div>
                </AccordionHeader>
                <AccordionContent>
                    <div v-if="successRows.length > 0">
                        <Table 
                            title="Success"
                            :headers="props.headers"
                            :rows="successRows"
                        />
                    </div>
                    <div v-else>
                        No Success Rows Present
                    </div>
                </AccordionContent>
            </AccordionPanel>
            <AccordionPanel value="1">
                <AccordionHeader>
                    <div class="header-container">
                        <div>Warnings</div>
                        <div>{{ props.warningRows.length }}</div>
                    </div>
                </AccordionHeader>
                <AccordionContent>
                    <div v-if="props.warningRows.length > 0">
                        <Table 
                            title="Warnings"
                            :headers="props.headers"
                            :rows="props.warningRows"
                        />
                    </div>
                    <div v-else>
                        No Warnings Present
                    </div>
                </AccordionContent>
            </AccordionPanel>
            <AccordionPanel value="3">
                <AccordionHeader>
                    <div class="header-container">
                        <div>Errors</div>
                        <div>{{ props.errorRows.length }}</div>
                    </div>
                </AccordionHeader>
                <AccordionContent>
                    <div v-if="props.errorRows.length > 0">
                        <Table 
                            title="Errors"
                            :headers="props.headers"
                            :rows="props.errorRows"
                        />
                    </div>
                    <div v-else>
                        No Errors Present
                    </div>
                </AccordionContent>
            </AccordionPanel>
        </Accordion>
    </div>
</template>

<style scoped>
.header-container{
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 2rem;
}
</style>