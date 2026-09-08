const CONFIG = {
  DATA_SHEET: 'ParsedStatements',
  ERROR_SHEET: 'Exceptions',
};

function processStatement(input) {
  const now = new Date().toISOString();
  const parser = getParser(input.carrier);

  if (!parser) {
    return logException({
      sourceFileId: input.sourceFileId,
      carrier: input.carrier || null,
      error: 'UNSUPPORTED_CARRIER',
      processedAt: now,
    });
  }

  try {
    const parsed = parser(input);
    const normalized = normalizeRecord(parsed, input, now);
    const errors = validateRecord(normalized);

    if (errors.length) {
      return logException({
        sourceFileId: input.sourceFileId,
        carrier: input.carrier,
        error: 'VALIDATION_FAILED',
        details: errors.join('; '),
        processedAt: now,
      });
    }

    upsertRecord(normalized);
    return normalized;
  } catch (err) {
    return logException({
      sourceFileId: input.sourceFileId,
      carrier: input.carrier || null,
      error: 'PARSER_ERROR',
      details: String(err && err.message ? err.message : err),
      processedAt: now,
    });
  }
}

function getParser(carrier) {
  const parsers = {
    ACME_INSURANCE: parseAcmeStatement,
  };
  return parsers[String(carrier || '').toUpperCase()] || null;
}

function normalizeRecord(parsed, input, processedAt) {
  const record = {
    carrier: input.carrier || null,
    statementDate: parsed.statementDate || null,
    accountNumber: parsed.accountNumber || null,
    grossAmount: numberOrNull(parsed.grossAmount),
    commissionAmount: numberOrNull(parsed.commissionAmount),
    netAmount: numberOrNull(parsed.netAmount),
    sourceFileId: input.sourceFileId || null,
    sourceFileName: input.sourceFileName || null,
    processedAt: processedAt,
  };

  record.recordKey = makeRecordKey(record);
  return record;
}

function validateRecord(record) {
  const errors = [];
  if (!record.sourceFileId) errors.push('sourceFileId is required');
  if (!record.carrier) errors.push('carrier is required');
  if (!record.statementDate) errors.push('statementDate is required');
  if (!record.accountNumber) errors.push('accountNumber is required');
  return errors;
}

function makeRecordKey(record) {
  const raw = [
    record.carrier,
    record.statementDate,
    record.accountNumber,
    record.sourceFileId,
  ].join('|');

  const bytes = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, raw);
  return bytes.map(function(b) {
    const v = (b < 0 ? b + 256 : b).toString(16);
    return v.length === 1 ? '0' + v : v;
  }).join('');
}

function upsertRecord(record) {
  const sheet = getOrCreateSheet(CONFIG.DATA_SHEET);
  const headers = [
    'recordKey', 'carrier', 'statementDate', 'accountNumber',
    'grossAmount', 'commissionAmount', 'netAmount',
    'sourceFileId', 'sourceFileName', 'processedAt'
  ];

  ensureHeaders(sheet, headers);
  const values = sheet.getDataRange().getValues();
  const keyIndex = headers.indexOf('recordKey');
  let targetRow = null;

  for (let r = 1; r < values.length; r++) {
    if (values[r][keyIndex] === record.recordKey) {
      targetRow = r + 1;
      break;
    }
  }

  const row = headers.map(function(h) { return record[h] == null ? '' : record[h]; });
  if (targetRow) {
    sheet.getRange(targetRow, 1, 1, row.length).setValues([row]);
  } else {
    sheet.appendRow(row);
  }
}

function logException(payload) {
  const sheet = getOrCreateSheet(CONFIG.ERROR_SHEET);
  const headers = ['sourceFileId', 'carrier', 'error', 'details', 'processedAt'];
  ensureHeaders(sheet, headers);
  sheet.appendRow(headers.map(function(h) { return payload[h] || ''; }));
  return payload;
}

function getOrCreateSheet(name) {
  const ss = SpreadsheetApp.getActive();
  return ss.getSheetByName(name) || ss.insertSheet(name);
}

function ensureHeaders(sheet, headers) {
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(headers);
    return;
  }

  const existing = sheet.getRange(1, 1, 1, headers.length).getValues()[0];
  if (existing.join('|') !== headers.join('|')) {
    throw new Error('Unexpected sheet schema for ' + sheet.getName());
  }
}

function numberOrNull(value) {
  if (value === null || value === undefined || value === '') return null;
  const cleaned = String(value).replace(/[$,]/g, '').trim();
  const n = Number(cleaned);
  return Number.isFinite(n) ? n : null;
}
