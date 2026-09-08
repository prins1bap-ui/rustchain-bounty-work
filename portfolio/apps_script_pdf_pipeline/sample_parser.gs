function parseAcmeStatement(input) {
  const text = String(input.extractedText || '');

  function capture(regex) {
    const match = text.match(regex);
    return match ? match[1].trim() : null;
  }

  return {
    statementDate: capture(/Statement Date\s*[:\-]\s*([^\n\r]+)/i),
    accountNumber: capture(/Account(?: Number| #)?\s*[:\-]\s*([^\n\r]+)/i),
    grossAmount: capture(/Gross(?: Amount)?\s*[:\-]\s*\$?([\d,]+(?:\.\d{2})?)/i),
    commissionAmount: capture(/Commission(?: Amount)?\s*[:\-]\s*\$?([\d,]+(?:\.\d{2})?)/i),
    netAmount: capture(/Net(?: Amount)?\s*[:\-]\s*\$?([\d,]+(?:\.\d{2})?)/i),
  };
}
