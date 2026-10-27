"""Replace only Pivot_Category with a native Excel PivotTable and slicers.

Run on Windows with Excel installed:
    .venv\\Scripts\\python.exe excel\\build_native_pivot.py

Uses the existing Orders_Clean table; never writes CSV or uses openpyxl to save.
All tests run before saving, and again after reopening the saved workbook.
"""

from hashlib import sha256
from math import isclose
from pathlib import Path
from zipfile import ZipFile
import json
import xml.etree.ElementTree as ET

import pandas as pd
import pythoncom
import win32com.client


ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "excel" / "Ecommerce_Sales_Excel_Report.xlsx"
CSV = ROOT / "ecommerce_sales.csv"
SHEET = "Pivot_Category"
PIVOT = "EcommerceCategoryRegion"
METRICS = (("sales", "Total Sales", -4157),
           ("profit", "Total Profit", -4157),
           ("order_id", "Order Count", -4112))  # xlSum, xlCount


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def snapshot(workbook):
    """Retain every other sheet's formulas/constants, tables and object counts."""
    result = {}
    for sheet in workbook.Worksheets:
        if sheet.Name == SHEET:
            continue
        used = sheet.UsedRange
        result[sheet.Name] = {
            "address": used.Address,
            "formulas_and_values": used.Formula,
            "tables": tuple((t.Name, t.Range.Address)
                            for t in sheet.ListObjects),
            "charts": sheet.ChartObjects().Count,
            "shapes": sheet.Shapes.Count,
        }
    return result


def totals(data):
    return (float(data.sales.sum()), float(data.profit.sum()),
            int(data.order_id.count()))


def check_totals(pivot, data, label):
    actual = tuple(float(pivot.GetPivotData(caption).Value)
                   for _, caption, _ in METRICS)
    expected = totals(data)
    require(all(isclose(a, e, rel_tol=0, abs_tol=0.00001)
                for a, e in zip(actual, expected)),
            f"{label}: native totals {actual} != CSV {expected}")
    return actual


def select_only(cache, name):
    # Select the target first: Excel will not allow deselecting the last item.
    cache.SlicerItems.Item(name).Selected = True
    for item in cache.SlicerItems:
        if item.Name != name:
            item.Selected = False
    require([item.Name for item in cache.SlicerItems if item.Selected] == [name],
            f"Slicer {cache.Name} did not select only {name}")


def validate_native(workbook, data):
    sheet = workbook.Worksheets(SHEET)
    require(sheet.PivotTables().Count == 1, "Expected one native PivotTable")
    pivot = sheet.PivotTables(PIVOT)
    require(pivot.PivotCache().SourceData == "Orders_Clean",
            "Pivot source must be the existing Orders_Clean table")
    require(pivot.PivotFields("category").Orientation == 1,
            "Category must be on rows")
    require(pivot.PivotFields("region").Orientation == 2,
            "Region must be on columns")
    require(pivot.DataFields.Count == 3, "Expected three value fields")
    for field, caption, function in METRICS:
        value = pivot.DataFields(caption)
        require(value.SourceName == field and value.Function == function,
                f"Wrong aggregation for {field}")

    region = workbook.SlicerCaches("EcommerceRegionCache")
    category = workbook.SlicerCaches("EcommerceCategoryCache")
    for cache, field in ((region, "region"), (category, "category")):
        require(cache.SourceName == field and not cache.OLAP,
                f"Wrong native slicer source for {field}")
        require(cache.PivotTables.Count == 1 and
                cache.PivotTables.Item(1).Name == PIVOT,
                f"{field} slicer must connect only to the new pivot")
        require(cache.Slicers.Count == 1 and
                cache.Slicers.Item(1).Shape.Parent.Name == SHEET,
                f"{field} slicer must live on {SHEET}")
        cache.ClearManualFilter()

    baseline = check_totals(pivot, data, "All orders")
    cases = 0
    # Each field alone and every intersection tests the actual native slicers.
    for cache, field in ((region, "region"), (category, "category")):
        for name in sorted(data[field].unique()):
            select_only(cache, name)
            check_totals(pivot, data[data[field] == name], f"{field}={name}")
            cache.ClearManualFilter()
            check_totals(pivot, data, f"Clear {field}={name}")
            cases += 1
    for region_name in sorted(data.region.unique()):
        select_only(region, region_name)
        for category_name in sorted(data.category.unique()):
            select_only(category, category_name)
            subset = data[(data.region == region_name) &
                          (data.category == category_name)]
            check_totals(pivot, subset, f"{region_name}/{category_name}")
            category.ClearManualFilter()
            check_totals(pivot, data[data.region == region_name],
                         "Clear category, retain region")
            cases += 1
        region.ClearManualFilter()
        check_totals(pivot, data, "Clear both slicers")
    require(all(item.Selected for cache in (region, category)
                for item in cache.SlicerItems), "Slicers must end unfiltered")

    workbook.Application.CalculateFullRebuild()
    quality = workbook.Worksheets("Quality_Checks").Range("A2:D10").Value
    require(all(row[3] == "PASS" for row in quality[:8]),
            f"Quality checks failed after recalculation: {quality}")
    require(quality[8][3] == "INFO" and
            quality[8][1] == int((data.profit < 0).sum()),
            "Loss-making informational check mismatch")
    return {"totals": baseline, "slicer_filter_cases": cases,
            "clear_restores_totals": True, "quality_checks_passed": 8,
            "loss_making_orders": int(quality[8][1])}


def build(workbook):
    sheet = workbook.Worksheets(SHEET)
    # Delete only slicer caches exclusively attached to the target sheet.
    # Refuse to disturb a slicer shared with another sheet on subsequent runs.
    for index in range(workbook.SlicerCaches.Count, 0, -1):
        cache = workbook.SlicerCaches.Item(index)
        linked = [p.Parent.Name for p in cache.PivotTables]
        destinations = [s.Shape.Parent.Name for s in cache.Slicers]
        if SHEET in linked or SHEET in destinations:
            require(all(name == SHEET for name in linked + destinations),
                    f"Refusing to remove shared slicer {cache.Name}")
            cache.Delete()
    for index in range(sheet.PivotTables().Count, 0, -1):
        sheet.PivotTables().Item(index).TableRange2.Clear()
    for index in range(sheet.Shapes.Count, 0, -1):
        sheet.Shapes.Item(index).Delete()
    sheet.Cells.UnMerge()
    sheet.Cells.Clear()
    sheet.Cells.Validation.Delete()
    sheet.Cells.FormatConditions.Delete()

    table = workbook.Worksheets("Clean_Data").ListObjects("Orders_Clean")
    require(table.DataBodyRange.Rows.Count == 2000,
            "Unexpected clean data row count")
    cache = workbook.PivotCaches().Create(SourceType=1,
                                         SourceData=table.Name, Version=6)
    pivot = cache.CreatePivotTable(TableDestination=sheet.Range("A5"),
                                  TableName=PIVOT)
    pivot.SaveData = True
    pivot.ManualUpdate = True
    pivot.PivotFields("category").Orientation = 1  # xlRowField
    pivot.PivotFields("category").Position = 1
    pivot.PivotFields("category").Subtotals = (False,) * 12
    pivot.PivotFields("region").Orientation = 2  # xlColumnField
    pivot.PivotFields("region").Position = 1
    for field, caption, function in METRICS:
        value = pivot.AddDataField(pivot.PivotFields(field), caption, function)
        value.NumberFormat = "#,##0" if field == "order_id" else "#,##0.00"
    pivot.DataPivotField.Orientation = 2
    pivot.DataPivotField.Position = 2
    pivot.RowAxisLayout(1)  # xlTabularRow
    pivot.RowGrand = True
    pivot.ColumnGrand = True
    pivot.TableStyle2 = "PivotStyleMedium9"
    pivot.ManualUpdate = False
    pivot.RefreshTable()

    sheet.Range("A1:P1").Merge()
    sheet.Range("A1").Value = "Category sales, profit and orders by region"
    sheet.Range("A1").Font.Size = 18
    sheet.Range("A1").Font.Bold = True
    sheet.Range("A1").Font.Color = 0x603020
    sheet.Range("A2").Value = (
        "Native PivotTable | Source: Orders_Clean | "
        "Use Region and Category slicers; clear filters to restore all orders."
    )
    sheet.Range("A2").Font.Size = 10
    sheet.Range("A:A").ColumnWidth = 22
    sheet.Range("B:P").ColumnWidth = 17
    sheet.Range("Q:Q").ColumnWidth = 3
    sheet.Range("R:T").ColumnWidth = 12
    left = sheet.Range("R5").Left
    top = sheet.Range("R5").Top
    for field, name, caption, offset, height in (
            ("region", "EcommerceRegion", "Region", 0, 170),
            ("category", "EcommerceCategory", "Category", 185, 205)):
        slicer_cache = workbook.SlicerCaches.Add2(
            pivot, field, name + "Cache")
        slicer = slicer_cache.Slicers.Add(
            SlicerDestination=sheet, Name=name + "Slicer", Caption=caption,
            Top=top + offset, Left=left, Width=225, Height=height)
        slicer.Style = "SlicerStyleLight2"
        slicer.NumberOfColumns = 1
    sheet.Activate()
    workbook.Windows(1).Zoom = 75
    sheet.Range("A1").Select()


def validate_package():
    with ZipFile(WORKBOOK) as package:
        names = package.namelist()
        parts = {kind: [name for name in names
                        if name.startswith(prefix) and name.endswith(".xml")]
                 for kind, prefix in (
                     ("pivot_tables", "xl/pivotTables/pivotTable"),
                     ("pivot_cache_definitions", "xl/pivotCache/pivotCacheDefinition"),
                     ("pivot_cache_records", "xl/pivotCache/pivotCacheRecords"),
                     ("slicers", "xl/slicers/slicer"),
                     ("slicer_caches", "xl/slicerCaches/slicerCache"))}
        require(all(parts.values()), f"Missing native OOXML parts: {parts}")
        pivots = [ET.fromstring(package.read(name))
                  for name in parts["pivot_tables"]]
        require(any(p.attrib.get("name") == PIVOT for p in pivots),
                "Saved native pivot definition missing")
        definitions = [ET.fromstring(package.read(name))
                       for name in parts["pivot_cache_definitions"]]
        require(any(any(node.attrib.get("name") == "Orders_Clean"
                        for node in definition.iter()) and
                    definition.attrib.get("recordCount") == "2000"
                    for definition in definitions),
                "Saved cache does not reference 2,000-row Orders_Clean table")
        return parts


def main():
    csv_hash = sha256(CSV.read_bytes()).hexdigest()
    data = pd.read_csv(CSV)
    pythoncom.CoInitialize()
    excel = None
    workbook = None
    try:
        excel = win32com.client.DispatchEx("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        excel.EnableEvents = False
        excel.AskToUpdateLinks = False
        excel.AutomationSecurity = 3  # Disable macros for this private instance.
        workbook = excel.Workbooks.Open(str(WORKBOOK), UpdateLinks=0,
                                        ReadOnly=False)
        require(not workbook.ReadOnly, "Workbook is locked/read-only")
        before = snapshot(workbook)
        order = tuple(s.Name for s in workbook.Worksheets)
        build(workbook)
        initial = validate_native(workbook, data)
        require(snapshot(workbook) == before,
                "Another sheet's formulas, data, tables or objects changed")
        require(tuple(s.Name for s in workbook.Worksheets) == order,
                "Worksheet order changed")
        workbook.Save()
        workbook.Close(SaveChanges=False)
        workbook = None
        workbook = excel.Workbooks.Open(str(WORKBOOK), UpdateLinks=0,
                                        ReadOnly=True)
        saved = validate_native(workbook, data)
        require(saved == initial, "Saved workbook native tests differ")
        require(snapshot(workbook) == before,
                "Saved workbook changed another sheet")
        require(tuple(s.Name for s in workbook.Worksheets) == order,
                "Saved worksheet order changed")
        workbook.Close(SaveChanges=False)
        workbook = None
        parts = validate_package()
        require(sha256(CSV.read_bytes()).hexdigest() == csv_hash, "CSV changed")
        print(json.dumps({"workbook": str(WORKBOOK), "excel_version": excel.Version,
                          "native_validation_before_and_after_save": saved,
                          "other_sheets_preserved": list(before),
                          "csv_unchanged": True, "native_package_parts": parts},
                         indent=2))
    finally:
        if workbook is not None:
            workbook.Close(SaveChanges=False)
        if excel is not None:
            excel.Quit()
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    main()
