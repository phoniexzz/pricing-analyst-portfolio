import {Workbook} from '@oai/artifact-tool';
console.log(Workbook.create().help('enum.*',{search:'TickLabel|LabelPosition',include:'index,notes',maxChars:3500}).ndjson);
