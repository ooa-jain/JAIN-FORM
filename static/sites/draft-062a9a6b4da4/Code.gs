// ═══════════════════════════════════════════════════════
//  INTERN STAR — Google Apps Script
//  Deploy: Web App | Execute as: Me | Access: Anyone
//  After updating this file → Deploy → New version
// ═══════════════════════════════════════════════════════

const SHEET_NAME = "Submissions";

const COLUMNS = [
  "submitted_at","name","sid","prog","dur","company","origin","superpower",
  "skill","strategy","conf_b","conf_a",
  "problem","thinking","outcome","think_mode",
  "team","team_role","collab_win","collab_fail","role_style",
  "setback","time_mgmt","wellbeing","stress",
  "t_ai","t_collab","best_tool",
  "m1t","m1b","m2t","m2b","m3t","m3b",
  "contribution","value","school_back",
  "mentor_name","mentor_role","mentor_lesson","mentor_rating",
  "takeaways","goals","advice"
];

function doPost(e) {
  try {
    var ss    = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName(SHEET_NAME);
    if (!sheet) sheet = ss.insertSheet(SHEET_NAME);

    if (sheet.getLastRow() === 0) {
      sheet.appendRow(COLUMNS);
      var hdr = sheet.getRange(1, 1, 1, COLUMNS.length);
      hdr.setBackground("#1a1a2e");
      hdr.setFontColor("#FFE066");
      hdr.setFontWeight("bold");
      sheet.setFrozenRows(1);
    }

    // FormData fields come in as e.parameter
    var row = COLUMNS.map(function(col) {
      var val = e.parameter[col];
      return (val !== undefined && val !== null) ? String(val) : "";
    });

    sheet.appendRow(row);

    return ContentService
      .createTextOutput(JSON.stringify({ success: true }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch(err) {
    return ContentService
      .createTextOutput(JSON.stringify({ success: false, error: err.message }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  // Test by opening the URL in browser — should show this JSON
  return ContentService
    .createTextOutput(JSON.stringify({ status: "ok", message: "INTERN STAR live!" }))
    .setMimeType(ContentService.MimeType.JSON);
}
