import math
import NXOpen
import NXOpen.UF
import NXOpen.Features
import NXOpen.GeometricUtilities
import NXOpen.Annotations
import NXOpen.Assemblies
import NXOpen.Drawings


def main():
    theSession = NXOpen.Session.GetSession()
    workPart = theSession.Parts.Work
    theUI = NXOpen.UI.GetUI()
    lw = theSession.ListingWindow
    
    workPart.ModelingViews.WorkView.Orient(NXOpen.View.Canned.Isometric, NXOpen.View.ScaleAdjustment.Fit)
    workPart.ModelingViews.WorkView.RenderingStyle = NXOpen.View.RenderingStyleType.WireframeWithDimEdges

    response, selected_face = select_face(theUI, "Select Tube/Hose/Sleeve for Centerline")

    if response == NXOpen.Selection.Response.Ok:

        initial_centerline = None
        initial_length = 0.0

        virtualCurveBuilder1 = workPart.Features.CreateVirtualCurveBuilder(NXOpen.Features.VirtualCurve.Null)
        virtualCurveBuilder1.CurveFitData.Tolerance = 0.01
        virtualCurveBuilder1.CurveFitData.AngleTolerance = 0.5
        virtualCurveBuilder1.Type = NXOpen.Features.VirtualCurveBuilder.Types.TubeCenterline
        
        face1 = selected_face
        faceTangentRule1 = workPart.ScRuleFactory.CreateRuleFaceTangent(face1, [], 0.5, workPart.ScRuleFactory.CreateRuleOptions())
        virtualCurveBuilder1.TubeFaces.ReplaceRules([faceTangentRule1], False)
        
        nXObject1 = virtualCurveBuilder1.Commit()
        curves = nXObject1.GetEntities()
        
        if not curves:
            theUI.NXMessageBox.Show("Error", NXOpen.NXMessageBox.DialogType.Error, "No Curves Generated.")
            return
        
        total_length = 0.0
        all_curves = []
        
        for curve in curves:
            try:
                if hasattr(curve, 'GetLength'):
                    length = curve.GetLength()
                else:
                    theUfSession = NXOpen.UF.UFSession.GetUFSession()
                    measure = theUfSession.Modl.AskLengthOfObject(curve.Tag)
                    length = measure.length

                total_length += length
                all_curves.append(curve)

            except Exception as e:
                    theUI.NXMessageBox.Show("Error", NXOpen.NXMessageBox.DialogType.Error, f"Error while measuring: {str(e)}")
                    return

        workPart.ModelingViews.WorkView.Orient(NXOpen.View.Canned.Isometric, NXOpen.View.ScaleAdjustment.Fit)
        workPart.ModelingViews.WorkView.RenderingStyle = NXOpen.View.RenderingStyleType.WireframeWithDimEdges


        # Create Edge Diameter Dimension
        selection = theUI.SelectionManager

        response, selected_objects = theUI.SelectionManager.SelectObjects(
            'Select Edge', 
            'Select Edge to Get Diameter', 
            NXOpen.Selection.SelectionScope.AnyInAssembly, 
            False, 
            [NXOpen.Selection.SelectionType.Edges])

        if response == NXOpen.Selection.Response.Ok and selected_objects:
            edge = selected_objects[0]
            vertices = edge.GetVertices()

            if len(vertices) >= 2:
                start_point = vertices[0]
                end_point = vertices[-1]
                center_point = NXOpen.Point3d(
                    (start_point.X + end_point.X)/2,
                    (start_point.Y + end_point.Y)/2,
                    (start_point.Z + end_point.Z)/2
                    )
            else:
                curve = edge.GetGeometry()
                start_point = curve.Evaluate(0.0)
                end_point = curve.Evaluate(1.0)
                center_point = NXOpen.Point3d(
                (start_point.X + end_point.X)/2,
                (start_point.Y + end_point.Y)/2,
                (start_point.Z + end_point.Z)/2
                )
            
            markId1 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Start")

            pmiRadialDimensionBuilder1 = workPart.Dimensions.CreatePmiRadialDimensionBuilder(NXOpen.Annotations.Dimension.Null)
            pmiRadialDimensionBuilder1.Style.LetteringStyle.DimensionTextSize = 20.5
            pmiRadialDimensionBuilder1.Style.LetteringStyle.AppendedTextSize = 20.5
            pmiRadialDimensionBuilder1.Style.LetteringStyle.ToleranceTextSize = 20.5
            pmiRadialDimensionBuilder1.Style.LetteringStyle.TwoLineToleranceTextSize = 20.5
            pmiRadialDimensionBuilder1.Style.LineArrowStyle.ArrowheadLength = 20.5
            pmiRadialDimensionBuilder1.FirstAssociativity.SetValue(edge, workPart.ModelingViews.WorkView, center_point)

            point2 = NXOpen.Point3d(0.0, 0.0, 0.0)
            pmiRadialDimensionBuilder1.FirstAssociativity.SetValue(NXOpen.InferSnapType.SnapType.NotSet, edge, workPart.ModelingViews.WorkView, center_point, NXOpen.TaggedObject.Null, NXOpen.View.Null, point2)

            objects1 = [NXOpen.NXObject.Null] * 1 
            objects1[0] = edge

            pmiRadialDimensionBuilder1.AssociatedObjects.Nxobjects.SetArray(objects1)
            pmiRadialDimensionBuilder1.Origin.Plane.PlaneMethod = NXOpen.Annotations.PlaneBuilder.PlaneMethodType.ModelView
            pmiRadialDimensionBuilder1.Origin.SetInferRelativeToGeometry(True)
            nXObject1 = pmiRadialDimensionBuilder1.Commit()

            suppressPMIBuilder1 = workPart.PmiManager.CreateSuppressPmibuilder()
            suppressPMIBuilder1.SuppressionMethod = NXOpen.Annotations.SuppressPMIBuilder.SuppressionMethodType.Manual
            theSession.SetUndoMarkName(markId1, "Suppress PMI Object Dialog")

            added1 = suppressPMIBuilder1.SelectPMIObjects.Add(nXObject1)
            nXObject2 = suppressPMIBuilder1.Commit()
            suppressPMIBuilder1.Destroy()
        
            dimension_value = ""
            if isinstance(nXObject1, NXOpen.Annotations.Dimension):
                try:
                    
                    dimension_value = nXObject1.GetMeasurement().Value
                    if isinstance(dimension_value, tuple):
                        dimension_value = dimension_value[0]
                    dimension_value = float(dimension_value)
                    
                    dim_text = str(nXObject1.GetDimensionText()).upper()
                    
                    if ('R' in dim_text or 'RAD' in dim_text) and not ('Ø' in dim_text or 'DIA' in dim_text):
                        dimension_value *= 2
                        dim_type = "(converted from Radius)"
                    else:
                        dim_type = "(Diameter)"
                    
                    dimension_value = f"{dimension_value:.2f}"
                    
                except:
                    try:
                        dimension_text = nXObject1.GetDimensionText()
                        import re
                        numeric_text = re.sub(r"[^\d.]", "", str(dimension_text))
                        if numeric_text:
                            dimension_value = f"{float(numeric_text):.2f}"
                        else:
                            dimension_value = "Unable to retrieve value"
                    except:
                        dimension_value = "Unable to retrieve value"
            
            info_msg = f"OD/ID: {dimension_value} mm {dim_type if 'dim_type' in locals() else ''}"
            lw.Open()
            lw.WriteLine(info_msg)

            theSession.DeleteUndoMark(markId1, None)
            pmiRadialDimensionBuilder1.Destroy()

        # Create OD/ID and Centerline Dimension for Expansion

        response = theUI.NXMessageBox.Show(
            "Create OD/ID Dimension For Expansion", NXOpen.NXMessageBox.DialogType.Question,
            "Do you want to create a OD/ID and Centerline for expansion?")

        if response == 1:
            
            while True:
                response2, selobj = select_face(theUI, "Select Tube/Hose/Sleeve Expansion")
                
                if response2 != NXOpen.Selection.Response.Ok:
                    break  
                
                expansion_curves = process_face(workPart, theUI, selobj)
                if expansion_curves:
                    all_curves.extend(expansion_curves)
            
            total_combined_length = 0.0
            for curve in all_curves:
                try:
                    if hasattr(curve, 'GetLength'):
                        length = curve.GetLength()
                    else:
                        theUfSession = NXOpen.UF.UFSession.GetUFSession()
                        measure = theUfSession.Modl.AskLengthOfObject(curve.Tag)
                        length = measure.length
                    
                    total_combined_length += length
                
                except Exception as e:
                    theUI.NXMessageBox.Show("Error", NXOpen.NXMessageBox.DialogType.Error, f"Error while measuring: {str(e)}")
                    return

            # Create edge diameter dimension for expansion (existing code remains the same)
            selection = theUI.SelectionManager

            response3, selected_objects = theUI.SelectionManager.SelectObjects(
                'Select Edge', 
                'Select Edge to Get Diameter', 
                NXOpen.Selection.SelectionScope.AnyInAssembly, 
                False, 
                [NXOpen.Selection.SelectionType.Edges])

            if response3 == NXOpen.Selection.Response.Ok and selected_objects:
                edge = selected_objects[0]
                vertices = edge.GetVertices()

                if len(vertices) >= 2:
                    start_point = vertices[0]
                    end_point = vertices[-1]
                    center_point = NXOpen.Point3d(
                        (start_point.X + end_point.X)/2,
                        (start_point.Y + end_point.Y)/2,
                        (start_point.Z + end_point.Z)/2
                        )
                else:
                    curve = edge.GetGeometry()
                    start_point = curve.Evaluate(0.0)
                    end_point = curve.Evaluate(1.0)
                    center_point = NXOpen.Point3d(
                    (start_point.X + end_point.X)/2,
                    (start_point.Y + end_point.Y)/2,
                    (start_point.Z + end_point.Z)/2
                    )
                
                markId1 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Start")

                pmiRadialDimensionBuilder1 = workPart.Dimensions.CreatePmiRadialDimensionBuilder(NXOpen.Annotations.Dimension.Null)
                pmiRadialDimensionBuilder1.Style.LetteringStyle.DimensionTextSize = 20.5
                pmiRadialDimensionBuilder1.Style.LetteringStyle.AppendedTextSize = 20.5
                pmiRadialDimensionBuilder1.Style.LetteringStyle.ToleranceTextSize = 20.5
                pmiRadialDimensionBuilder1.Style.LetteringStyle.TwoLineToleranceTextSize = 20.5
                pmiRadialDimensionBuilder1.Style.LineArrowStyle.ArrowheadLength = 20.5
                pmiRadialDimensionBuilder1.FirstAssociativity.SetValue(edge, workPart.ModelingViews.WorkView, center_point)

                point2 = NXOpen.Point3d(0.0, 0.0, 0.0)
                pmiRadialDimensionBuilder1.FirstAssociativity.SetValue(NXOpen.InferSnapType.SnapType.NotSet, edge, workPart.ModelingViews.WorkView, center_point, NXOpen.TaggedObject.Null, NXOpen.View.Null, point2)

                objects1 = [NXOpen.NXObject.Null] * 1 
                objects1[0] = edge

                pmiRadialDimensionBuilder1.AssociatedObjects.Nxobjects.SetArray(objects1)
                pmiRadialDimensionBuilder1.Origin.Plane.PlaneMethod = NXOpen.Annotations.PlaneBuilder.PlaneMethodType.ModelView
                pmiRadialDimensionBuilder1.Origin.SetInferRelativeToGeometry(True)
                nXObject1 = pmiRadialDimensionBuilder1.Commit()

                suppressPMIBuilder1 = workPart.PmiManager.CreateSuppressPmibuilder()
                suppressPMIBuilder1.SuppressionMethod = NXOpen.Annotations.SuppressPMIBuilder.SuppressionMethodType.Manual
                theSession.SetUndoMarkName(markId1, "Suppress PMI Object Dialog")

                added1 = suppressPMIBuilder1.SelectPMIObjects.Add(nXObject1)
                nXObject2 = suppressPMIBuilder1.Commit()
                suppressPMIBuilder1.Destroy()
                
                dimension_value = ""
                if isinstance(nXObject1, NXOpen.Annotations.Dimension):
                    try:
                        
                        dimension_value = nXObject1.GetMeasurement().Value
                        if isinstance(dimension_value, tuple):
                            dimension_value = dimension_value[0]
                        dimension_value = float(dimension_value)
                        
                        dim_text = str(nXObject1.GetDimensionText()).upper()
                        
                        if ('R' in dim_text or 'RAD' in dim_text) and not ('Ø' in dim_text or 'DIA' in dim_text):
                            dimension_value *= 2
                            dim_type = "(converted from Radius)"
                        else:
                            dim_type = "(Diameter)"
                        
                        dimension_value = f"{dimension_value:.2f}"
                        
                    except:
                        try:
                            dimension_text = nXObject1.GetDimensionText()
                            import re
                            numeric_text = re.sub(r"[^\d.]", "", str(dimension_text))
                            if numeric_text:
                                dimension_value = f"{float(numeric_text):.2f}"
                            else:
                                dimension_value = "Unable to retrieve value"
                        except:
                            dimension_value = "Unable to retrieve value"
                
                info_msg = f"EXPANSION OD/ID: {dimension_value} mm {dim_type if 'dim_type' in locals() else ''}"
                lw.Open()
                lw.WriteLine(info_msg)

                theSession.DeleteUndoMark(markId1, None)
                pmiRadialDimensionBuilder1.Destroy()

                theUI.NXMessageBox.Show("Completion", NXOpen.NXMessageBox.DialogType.Information, "Tube/Hose/Sleeve Expansion Centerline completed!")
            
        elif response == 2:
            response2 = theUI.NXMessageBox.Show(
                "Create OD/ID Dimension For Expansion", NXOpen.NXMessageBox.DialogType.Information,
                "No OD/ID Dimension Created for expansion.")
      
            pass

        # Create a point on the centerline - Modifty to make the note 

        if all_curves:
            markId1 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Create Point On the Curve")
            section = workPart.Sections.CreateSection(0.0095, 0.01, 0.5)
            section.SetAllowedEntityTypes(NXOpen.Section.AllowTypes.OnlyCurves)

            curve_for_annotation = all_curves[0]
            expression = workPart.Expressions.CreateSystemExpressionWithUnits("50", NXOpen.Unit.Null)
            scalar = workPart.Scalars.CreateScalarExpression(expression, 
                                                           NXOpen.Scalar.DimensionalityType.NotSet, 
                                                           NXOpen.SmartObject.UpdateOption.WithinModeling)
            
            point = workPart.Points.CreatePoint(curve_for_annotation, scalar, 
                                              NXOpen.PointCollection.PointOnCurveLocationOption.PercentArcLength, 
                                              None, 
                                              NXOpen.SmartObject.UpdateOption.WithinModeling)
            point.RemoveViewDependency()
            
            pointFeatureBuilder = workPart.BaseFeatures.CreatePointFeatureBuilder(None)
            pointFeatureBuilder.Point = point
            
            pointFeatureBuilder.Commit()
            theSession.SetUndoMarkName(markId1, "Point created")
            
            coordinates = point.Coordinates
            annotation_point = NXOpen.Point3d(coordinates.X, coordinates.Y, coordinates.Z)

            # Create annotation with total length
            annotation_centerline = workPart.MeasureManager.CreateNoteAnnotation(annotation_point, [f"Length: {total_combined_length:.2f} mm"])
            editSettingsBuilder = workPart.SettingsManager.CreateAnnotationEditSettingsBuilder([annotation_centerline])
            editSettingsBuilder.AnnotationStyle.LetteringStyle.GeneralTextColor = workPart.Colors.Find("Black")
            editSettingsBuilder.AnnotationStyle.LineArrowStyle.FirstArrowheadColor = workPart.Colors.Find("Black")
            editSettingsBuilder.AnnotationStyle.LineArrowStyle.FirstArrowLineColor = workPart.Colors.Find("Black")
            editSettingsBuilder.Commit()
            editSettingsBuilder.Destroy()
                

def select_face(theUI, title):
    response, selobj, _ = theUI.SelectionManager.SelectObject(
        "Select a face", title, NXOpen.Selection.SelectionScope.AnyInAssembly, False, 
        [NXOpen.Selection.SelectionType.Faces])
    return (NXOpen.Selection.Response.Ok, selobj) if response in [NXOpen.Selection.Response.ObjectSelected, NXOpen.Selection.Response.ObjectSelectedByName] else (NXOpen.Selection.Response.Cancel, None)

def get_unload_option(dummy):
    return NXOpen.Session.LibraryUnloadOption.Immediately

def process_face(workPart, theUI, face):
    virtualCurveBuilder1 = workPart.Features.CreateVirtualCurveBuilder(NXOpen.Features.VirtualCurve.Null)
    virtualCurveBuilder1.CurveFitData.Tolerance = 0.01
    virtualCurveBuilder1.CurveFitData.AngleTolerance = 0.5
    virtualCurveBuilder1.Type = NXOpen.Features.VirtualCurveBuilder.Types.TubeCenterline

    faceTangentRule1 = workPart.ScRuleFactory.CreateRuleFaceTangent(face, [], 0.5, workPart.ScRuleFactory.CreateRuleOptions())
    virtualCurveBuilder1.TubeFaces.ReplaceRules([faceTangentRule1], False)

    nXObject1 = virtualCurveBuilder1.Commit()
    curves = nXObject1.GetEntities()

    if not curves:
        theUI.NXMessageBox.Show("Error", NXOpen.NXMessageBox.DialogType.Error, "No Curves Generated.")
        return None

    expansion_curves = []
    

    for curve in curves:
        try:
            if hasattr(curve, 'GetLength'):
                length = curve.GetLength()
            else:
                theUfSession = NXOpen.UF.UFSession.GetUFSession()
                measure = theUfSession.Modl.AskLengthOfObject(curve.Tag)
                length = measure.length

            expansion_curves.append(curve)

        except Exception as e:
            theUI.NXMessageBox.Show("Error", NXOpen.NXMessageBox.DialogType.Error, f"Error while measuring: {str(e)}")
            return None

    centerline = nXObject1
    removeParametersBuilder2 = workPart.Features.CreateRemoveParametersBuilder()
    added2 = removeParametersBuilder2.Objects.Add(centerline)
    nXObject2 = removeParametersBuilder2.Commit()

    return expansion_curves
    

main()