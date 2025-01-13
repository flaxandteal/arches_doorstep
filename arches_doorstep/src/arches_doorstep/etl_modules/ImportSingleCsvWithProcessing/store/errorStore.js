import { reactive } from 'vue';

const state = reactive({
    errorCounts: 0,
    totalErrors: 0,
    infoTable: [],
    warningTable: [],
    errorTable: [],
    conceptHeaders: [],
    conceptSuccessRows: [],
    conceptErrorRows: [],
    conceptWarningRows: [],
    resourceHeaders: [],
    resourceSuccessRows: [],
    resourceErrorRows: [],
    resourceWarningRows: [],
    dateHeaders: [],
    dateErrorRows: [],
    dateWarningRows: [],
    fileConverted: false,
    conversionError: false
});

const processDates = (table, code) => {
    const headers = new Set();
    const warningRows = [];
    const errorRows = [];

    table
        .filter((entry) => entry.code === code)
        .forEach((entry) => {
            const item = entry["error-data"];
            const row = { 
                "Column": item.column_name, 
                "Column No.": item.column_id,
                "Row No.": item.row_id,
                "Column Entry": item.value, 
                "Closest Match": item.suggested_accepted_value ?? "Null",  
            };
            Object.keys(row).forEach((key) => headers.add(key));
            if (item.suggested_accepted_value) {
                warningRows.push(row);
            } else {
                errorRows.push(row);
            }
        }
        );
        

    return { headers: Array.from(headers), warningRows, errorRows };
};

const processData = (table, code) => {
    if (!table || table.length === 0) return { headers: [], successRows: [], warningRows: [], errorRows: [] };

    const headers = new Set();
    const successRows = [];
    const warningRows = [];
    const errorRows = [];

    table
        .filter((entry) => entry.code === code)
        .forEach((entry) => {
            const data = JSON.parse(entry["error-data"]);
            for (const item of data) {
                const row = { 
                    "Column": item.column, 
                    "Column No.": item.column_index,
                    "Row No.": item.row_index,
                    "Column Entry": item.original_entry, 
                    "Closest Match": item.closest_match ?? "Null", 
                    "Match Percentage": parseInt(item.match_percentage ?? 0, 10), 
                    "Closest Match ID": item.closest_match_id ?? "Null" 
                };
                headers.add("Column");
                headers.add("Column No.");
                headers.add("Row No.");
                headers.add("Column Entry");
                headers.add("Closest Match");
                headers.add("Match Percentage");
                headers.add("Closest Match ID");

                if (row["Match Percentage"] === 100) {
                    successRows.push(row);
                } else if (row["Match Percentage"] > 0) {
                    warningRows.push(row);
                } else {
                    errorRows.push(row);
                }
            }
        });
    return { headers: Array.from(headers), successRows, warningRows, errorRows };
};

const updateTables = () => {
    const conceptData = processData(state.infoTable, "mapping-concept-summary");
    state.conceptHeaders = conceptData.headers;
    state.conceptSuccessRows = conceptData.successRows;
    state.conceptErrorRows = conceptData.errorRows;
    state.conceptWarningRows = conceptData.warningRows;

    const resourceData = processData(state.infoTable, "mapping-resource-summary");
    state.resourceHeaders = resourceData.headers;
    state.resourceSuccessRows = resourceData.successRows;
    state.resourceErrorRows = resourceData.errorRows;
    state.resourceWarningRows = resourceData.warningRows;

    const dateData = processDates(state.warningTable, "Date-category");
    state.dateHeaders = dateData.headers;
    state.dateErrorRows = dateData.errorRows;
    state.dateWarningRows = dateData.warningRows;
};

const setInfoTable = (data) => {
    state.infoTable = data || [];
    updateTables();
};

const setWarningTable = (data) => {
    state.warningTable = data || [];
    updateTables();
};

const resetErrorStore = () => {
    state.errorCounts = 0;
    state.totalErrors = 0;
    state.infoTable = [];
    state.warningTable = [];
    state.errorTable = [];
    state.conceptHeaders = [];
    state.conceptSuccessRows = [];
    state.conceptErrorRows = [];
    state.conceptWarningRows = [];
    state.resourceHeaders = [];
    state.resourceSuccessRows = [];
    state.resourceErrorRows = [];
    state.resourceWarningRows = [];
    state.dateHeaders = [];
    state.dateWarningRows = [];
    state.dateErrorRows = [];
    state.fileConverted = false;
}

export default {
    state,
    setInfoTable,
    setWarningTable,
    updateTables,
    resetErrorStore
};