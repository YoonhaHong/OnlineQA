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

plane_colors = {
    0: ROOT.kRed,
    1: ROOT.kBlue,
    2: ROOT.kGreen+2,
    3: ROOT.kMagenta,
    4: ROOT.kCyan+2,
    5: ROOT.kOrange+7,
    6: ROOT.kViolet
}

def draw_fit_result(fit_result, precision=0):
    """
    Drawing the mean and sigma values from a fit result on the current canvas.
    :param fit_result: ROOT TF1 fit result object
    :param precision: Number of decimal places to display for mean and sigma (default is 0)
    """
    if fit_result is not None :
        mean_x = fit_result.Parameter(1)
        sigma_x = fit_result.Parameter(2)
        latex_x = TLatex()
        latex_x.SetTextSize(0.08)
        latex_x.SetTextColor(2) 
        latex_x.DrawLatexNDC(0.15, 0.82, f"Mean: {mean_x:.{precision}f}")
        latex_x.DrawLatexNDC(0.15, 0.72, f"Sigma: {sigma_x:.{precision}f}")

def plot_beamstr(args):

    analyse_root = ROOT.TFile.Open(args.inputfile,"READ")
    _planes = [f"ALPIDE_{i}" for i in range(15)] 
    planes = []
    for plane in _planes:
        if hasattr(analyse_root.EventLoaderEUDAQ2, plane): planes.append(plane)
    print("Detected planes: ", planes)
    nplane = len(planes)

    c1 = ROOT.TCanvas('c1', 'c1', 900*nplane, 3000)
    #                                        x1,  y1,  x2,  y2)
    pad1 = ROOT.TPad("pad1","This is pad1",0.01,0.92,0.99,0.99) # title and rate info
    pad2 = ROOT.TPad("pad3","This is pad3",0.01,0.42,0.99,0.92) # hitmaps and projections
    pad4 = ROOT.TPad("pad4","This is pad4",0.01,0.22,0.99,0.42) # correlations
    pad3 = ROOT.TPad("pad2","This is pad2",0.01,0.01,0.99,0.42) # track angles and chi2ndof

    pad1.Draw()
    pad2.Draw()
    pad4.Draw()
    pad3.Draw()
    # print LABEL
    pad1.cd()
    title = ROOT.TLatex()
    title.SetTextSize(0.3)
    title.DrawLatex(.05,0.1,str(args.canvastitle))
    info = ROOT.TLatex()
    info.SetTextSize(0.3)
    infostr=""
    info.DrawLatex(.05,0.5,infostr)
    #draw_beam_rate(analyse_root, args.inputfile.replace('./plots/QA_beamstr', f'./data').replace('analyse_', '').replace('_a.root', '.raw').replace('.root', '.raw'))
    # gStyle options
    ROOT.gStyle.SetOptStat("emr")
    ROOT.gStyle.SetPadRightMargin(0.10)
    ROOT.gStyle.SetPadLeftMargin(0.10)
    ROOT.gStyle.SetPadTopMargin(0.09)
    ROOT.gStyle.SetPadBottomMargin(0.09)

    # print ALPIDE hitmaps
    pad_index = 1
    pad2.cd()
    pad2.Divide(nplane, 3)

    for plane in planes:
        for t in range(4):
           
            pad2.cd(pad_index + nplane * t)
            ROOT.gStyle.SetTextSize(0.1)
            if t == 0:
                clustermap = analyse_root.Get(f"EventLoaderEUDAQ2/{plane}/hitmap")
                clustermap.Rebin2D(16, 16)
                clustermap.Draw("COLZ")
            elif t == 1:
                hitmap = analyse_root.Get(f"ClusteringSpatial/{plane}/clusterPositionLocal")
                x_proj = hitmap.ProjectionX()
                x_proj.SetNameTitle(f"{plane}_xproj", f"{plane} projection X")
                fit_projX = x_proj.Fit("gaus", "SQ") 
                draw_fit_result(fit_projX)
            elif t == 2:
                hitmap = analyse_root.Get(f"ClusteringSpatial/{plane}/clusterPositionLocal")
                y_proj = hitmap.ProjectionY()
                y_proj.SetNameTitle(f"{plane}_yproj", f"{plane} projection Y")
                fit_projY = y_proj.Fit("gaus", "SQ")
                draw_fit_result(fit_projY)
            # elif t ==3:
            # TBA
            else:
                pad_index += 1
    
    pad3.cd()

    corr_hists = []
    corrX_mean = []
    corrY_mean = []
    corrX_sigma = []
    corrY_sigma = []
    for plane in planes:
        #if int(plane[-1]) == 0: continue
        for i in ['X', 'Y']:
            #x_proj = getattr(analyse_root.Correlations, plane).Get("correlation"+i)
            x_proj = analyse_root.Get(f"Correlations/{plane}/correlation{i}")
            # x_proj.Rebin(16)
            x_proj.SetNameTitle(f"{plane}_{i}corr", f"{i}_0 - {i} correlations")
            x_proj.SetLineColor(plane_colors[int(plane[-1])])
            x_proj.GetXaxis().SetRangeUser(-5., 5.)
            x_proj.GetYaxis().SetTitle("entries")
            #x_proj.Draw("SAME")
            fit_projX = x_proj.Fit("gaus", "SQ")
            corr_hists.append(x_proj)

            if fit_projX.IsValid():
                mean = fit_projX.Parameter(1)
                sigma= fit_projX.Parameter(2)

            else:
                mean = float('nan')
                sigma = float('nan')


            if i =='X':
                corrX_mean.append(mean)
                corrX_sigma.append(sigma)
            else:
                corrY_mean.append(mean)
                corrY_sigma.append(sigma)
    
    print(corrX_mean)
    print(corrY_mean)
    # print ALPIDE correlations
    zeroline = ROOT.TLine(0, 0, 6.5, 0)
    zeroline.SetLineColor(ROOT.kGray)
    zeroline.SetLineStyle(2)
    #pad3.Divide(2)
    pad3.cd(1)
    graphX = ROOT.TGraphErrors(len(planes))
    graphX.SetPoint(0, 0, 0)  # Dummy point
    graphX.SetPointError(0, 0, 0)
    for i, plane in enumerate(planes):
        graphX.SetPoint(i+1, int(plane[-1]), corrX_mean[i])
        graphX.SetPointError(i+1, 0, corrX_sigma[i])
    graphX.SetTitle("X Correlations;Ref Plane Index;X_{ref} - X [mm]")
    graphX.SetMarkerStyle(21)
    graphX.Draw("AP")
    zeroline.Draw("SAME")
    


    
    _file_path = os.path.join(args.outputdir, args.canvastitle + ".pdf")
    c1.Print(_file_path)
    #c1.Update()
    #ROOT.gPad.Update()
    try:
        input("Press any key to exit")
    except EOFError:
        pass

def get_arguments():
    parser=argparse.ArgumentParser(description='QA tool for Physically Aligning Telescope', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('inputfile', type=str, help='Raw-data-file to QA.')
    parser.add_argument('--canvastitle',  '-t', type=str, default='runXXX', help='Canvas title.')
    parser.add_argument('--outputdir',  '-o', type=str, default='./output', help='Output directory.')
    args=parser.parse_args()
    return args

if __name__=="__main__":
    args=get_arguments()
    plot_beamstr(args)
