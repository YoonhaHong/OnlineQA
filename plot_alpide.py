#!/usr/bin/env python3

import sys, argparse
import shutil
from rich import print
from tqdm import tqdm
import os
import subprocess
import configparser
import platform

import ROOT
from ROOT import TLatex, TCanvas, TPad, TH1, TH2
#ROOT.gROOT.SetBatch(True)

def draw_fit_result(fit_result, precision=0):
    """
    Drawing the mean and sigma values from a fit result on the current canvas.
    :param fit_result: ROOT TF1 fit result object
    :param precision: Number of decimal places to display for mean and sigma (default is 0)
    """
    if fit_result is not None :
        mean_x = fit_result.Parameter(1)
        sigma_x = fit_result.Parameter(2)
        latex_x = ROOT.TLatex()
        latex_x.SetTextSize(0.08)
        latex_x.SetTextColor(2) 
        latex_x.DrawLatexNDC(0.15, 0.82, f"Mean: {mean_x:.{precision}f}")
        latex_x.DrawLatexNDC(0.15, 0.72, f"Sigma: {sigma_x:.{precision}f}")

def load_detector_histograms(input_file, prefix="ALPIDE"):
    root_file = ROOT.TFile.Open(input_file, "READ")
    if not root_file or root_file.IsZombie():
        raise RuntimeError(f"Could not open ROOT file: {input_file}")
    hitmaps = []
    correlationXs = []
    correlationYs = []

    correlations_dir = root_file.Get("Correlations")
    if not correlations_dir:
        raise RuntimeError("No 'Correlations' directory found in the ROOT file")
    
    for key in correlations_dir.GetListOfKeys():
        if not key.IsFolder():
            continue

        det_name = key.GetName()
        if not det_name.startswith(prefix):
            continue

        det_dir = correlations_dir.Get(det_name)
        if not det_dir:
            continue

        hitmap = det_dir.Get("hitmap_clusters")

        correlationX = root_file.Get(f"Prealignment/{det_name}/correlationX")
        correlationY = root_file.Get(f"Prealignment/{det_name}/correlationY")

        for hist in [hitmap, correlationX, correlationY]:
            if not hist:
                raise RuntimeError(f"Histogram not found for detector {det_name}")
            else:
                hist.SetDirectory(0)  # Detach histogram from the file

                
        hitmaps.append(hitmap)
        correlationXs.append(correlationX)
        correlationYs.append(correlationY)

    root_file.Close()
    return hitmaps, correlationXs, correlationYs

def draw_canvas(hitmaps, correlationXs, correlationYs, canvas_name):
    # gStyle options
    ROOT.gStyle.SetOptStat("emr")
    ROOT.gStyle.SetPadRightMargin(0.10)
    ROOT.gStyle.SetPadLeftMargin(0.10)
    ROOT.gStyle.SetPadTopMargin(0.09)
    ROOT.gStyle.SetPadBottomMargin(0.09)
    
    nplane = len(hitmaps)
    c1 = ROOT.TCanvas('c1', 'c1', 300*nplane, 1000)
    #                                        x1,  y1,  x2,  y2)
    pad1 = ROOT.TPad("pad1","Title",0.01,0.92,0.99,0.99) 
    pad2 = ROOT.TPad("pad2","Hitmaps",0.01,0.42,0.99,0.92) # hitmaps and projections
    pad4 = ROOT.TPad("pad4","Correlations",0.01,0.01,0.99,0.42) # correlations

    pad1.Draw()
    pad2.Draw()
    pad4.Draw()

    pad1.cd()
    title = ROOT.TLatex(0.05, 0.1, canvas_name)
    title.SetTextSize(0.3)
    title.Draw()

    pad2.Divide(nplane, 3)
    pad2.cd()
    for i, hitmap in enumerate(hitmaps):
        pad2.cd(i+1)
        #hitmap.SetTitle(f"{prefix} {i+1} Hitmap")
        hitmap.Rebin2D(16, 16)  # Rebin the hitmap for better visibility
        hitmap.Draw("colz")

        hitmap_clone = hitmap.Clone(f"hitmap_clone_{i}")
        projectionX = hitmap_clone.ProjectionX(f"projectionX_{i}")
        projectionY = hitmap_clone.ProjectionY(f"projectionY_{i}")

        pad2.cd(i+nplane+1)
        #projectionX.SetTitle(f"{prefix} {i+1} Projection X")
        fit_projectionX = projectionX.Fit("gaus", "SQ")  # Fit with Gaussian
        projectionX.Draw()
        draw_fit_result(fit_projectionX)  # Draw fit result on the histogram

        pad2.cd(i+nplane*2+1)
        #projectionY.SetTitle(f"{prefix} {i+1} Projection Y")
        fit_projectionY = projectionY.Fit("gaus", "SQ")  # Fit with Gaussian
        projectionY.Draw()
        draw_fit_result(fit_projectionY)  # Draw fit result on the histogram
    
    pad4.cd()
    graph_correlationX = ROOT.TGraphErrors(nplane)
    #graph_correlationX.SetPoint(0, 0, 0)  # Initialize the first point
    #graph_correlationX.SetPointError(0, 0, 0)  # Initialize the first point error
    for i, correlationX in enumerate(correlationXs):
        meanX = correlationX.GetMean()
        sigmaX = correlationX.GetRMS()
        graph_correlationX.SetPoint(i, i, meanX)
        graph_correlationX.SetPointError(i, 0, sigmaX)
    graph_correlationX.SetTitle("X Correlations;Ref Plane Index;X_{ref} - X [mm]")
    graph_correlationX.SetMarkerStyle(21)
    graph_correlationX.Draw("AP")

    zeroline = ROOT.TLine(0, 0, 6.5, 0)
    zeroline.SetLineColor(ROOT.kGray)
    zeroline.SetLineStyle(2)
    zeroline.Draw("SAME")

    # Keep Python-owned primitives alive after this function returns.
    c1._draw_objects = [title, graph_correlationX, zeroline]
    c1.Modified()
    c1.Update()
    return c1


def main():
    parser=argparse.ArgumentParser(description='QA tool for Physically Aligning Telescope', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("input_file", help="Path to the ROOT file")
    parser.add_argument('-t', '--canvastitle', type=str, default='runXXX', help='Canvas title.')
    parser.add_argument("-o", "--output", default="./output/telescope", help="Output PNG file")
    parser.add_argument("--show", action="store_true", help="Open the canvases in a window if DISPLAY is available")
    args = parser.parse_args()

    hitmaps, correlationXs, correlationYs = load_detector_histograms(args.input_file)
    c1 = draw_canvas(hitmaps, correlationXs, correlationYs, args.canvastitle)



    if args.show:
        c1.Show()
        ROOT.gApplication.Run()
            
        # if os.environ.get("DISPLAY"):
        #     
        # else:
        #     print("DISPLAY is not set; the canvases were saved as PDFs but could not be shown interactively.")
    c1.SaveAs(f"{args.output}.png")
    print(f"Saved: {args.output}.png")

if __name__=="__main__":
    main()
