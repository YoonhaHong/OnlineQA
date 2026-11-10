#!/usr/bin/env python3
import argparse
import os
import re
import ROOT

ROOT.gROOT.SetBatch(False)
REF_NAME = "ALPIDE_2"

def sort_detector_name(det_name):
    match = re.search(r"P(\d+)", det_name)
    if match:
        return (int(match.group(1)), det_name)
    return (10**9, det_name)


def load_detector_histograms(input_file, prefix="MOSAIX_UTA"):
    root_file = ROOT.TFile.Open(input_file, "READ")
    if not root_file or root_file.IsZombie():
        raise RuntimeError(f"Could not open ROOT file: {input_file}")

    correlations_dir = root_file.Get("Correlations")
    if not correlations_dir:
        raise RuntimeError("No 'Correlations' directory found in the ROOT file")

    histograms = []
    for key in correlations_dir.GetListOfKeys():
        if not key.IsFolder():
            continue

        det_name = key.GetName()
        if not det_name.startswith(prefix):
            continue

        det_dir = correlations_dir.Get(det_name)
        if not det_dir:
            continue

        hitmap_hist = det_dir.Get("hitmap_clusters")
        col_hist = det_dir.Get("correlationColCol_px")
        row_hist = det_dir.Get("correlationRowRow_px")
        if hitmap_hist and col_hist and row_hist:
            hitmap_clone = hitmap_hist.Clone()
            col_clone = col_hist.Clone()
            row_clone = row_hist.Clone()
            for hist in (hitmap_clone, col_clone, row_clone):
                hist.SetDirectory(0)
            histograms.append((det_name, hitmap_clone, col_clone, row_clone))

    root_file.Close()
    return sorted(histograms, key=lambda item: sort_detector_name(item[0]))


def find_histogram(histograms, p_number):
    for det_name, hitmap_hist, col_hist, row_hist in histograms:
        if f"P{p_number}" in det_name:
            return det_name, hitmap_hist, col_hist, row_hist
    return None


def draw_canvas(histograms, canvas_name, p_numbers, output_file):
    ROOT.gStyle.SetOptStat(0)
    canvas = ROOT.TCanvas(canvas_name, canvas_name, 1800, 1200)
    canvas.Divide(3, 3)

    for col_idx, p_number in enumerate(p_numbers):
        for row_idx, plot_name in enumerate(["hitmap_clusters", "correlationColCol_px", "correlationRowRow_px"]):
            pad = canvas.cd(row_idx * 3 + col_idx + 1)
            pad.Clear()
            pad.SetMargin(0.12, 0.16, 0.12, 0.12)

            entry = find_histogram(histograms, p_number)
            if not entry:
                continue

            det_name, hitmap_hist, col_hist, row_hist = entry
            if plot_name == "hitmap_clusters":
                hitmap_hist.SetTitle(f"{det_name} - hitmap_clusters;col;row")
                hitmap_hist.SetStats(0)
                hitmap_hist.Draw("COLZ")
            elif plot_name == "correlationColCol_px":
                col_hist.SetTitle(f"{det_name} - correlationColCol_px;{REF_NAME} col;{det_name} col")
                col_hist.SetStats(0)
                col_hist.Draw("COLZ")
            else:
                row_hist.SetTitle(f"{det_name} - correlationRowRow_px;{REF_NAME} row;{det_name} row")
                row_hist.SetStats(0)
                row_hist.Draw("COLZ")
    canvas.Update()
    canvas.Print(output_file)
    return canvas

    # canvas.Draw()


def main():
    parser = argparse.ArgumentParser(description="Plot MOSAIX_UTA hitmap_clusters / correlationColCol_px / correlationRowRow_px histograms in BAM and SEG canvases")
    parser.add_argument("input_file", help="Path to the ROOT file")
    parser.add_argument("-o", "--output", default="./output/mosaix_test", help="Output PNG file")
    parser.add_argument("--prefix", default="MOSAIX_UTA", help="Detector name prefix")
    parser.add_argument("--show", action="store_true", help="Open the canvases in a window if DISPLAY is available")
    args = parser.parse_args()

    histograms = load_detector_histograms(args.input_file, prefix=args.prefix)
    if not histograms:
        raise RuntimeError(f"No detectors matching prefix '{args.prefix}' with hitmap_clusters, correlationColCol_px and correlationRowRow_px were found")

    bam_output = args.output + ".png"

    c1 = draw_canvas(histograms, "canvasBAM", [6, 7, 8], bam_output)


    if args.show:
        c1.Show()
        ROOT.gApplication.Run()
            
        # if os.environ.get("DISPLAY"):
        #     
        # else:
        #     print("DISPLAY is not set; the canvases were saved as PDFs but could not be shown interactively.")
    print(f"Saved: {bam_output}")

if __name__ == "__main__":
    main()
