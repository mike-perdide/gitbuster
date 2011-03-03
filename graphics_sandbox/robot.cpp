/****************************************************************************
 **
 ** Copyright (C) 2011 Nokia Corporation and/or its subsidiary(-ies).
 ** All rights reserved.
 ** Contact: Nokia Corporation (qt-info@nokia.com)
 **
 ** This file is part of the examples of the Qt Toolkit.
 **
 ** $QT_BEGIN_LICENSE:BSD$
 ** You may use this file under the terms of the BSD license as follows:
 **
 ** "Redistribution and use in source and binary forms, with or without
 ** modification, are permitted provided that the following conditions are
 ** met:
 **   * Redistributions of source code must retain the above copyright
 **     notice, this list of conditions and the following disclaimer.
 **   * Redistributions in binary form must reproduce the above copyright
 **     notice, this list of conditions and the following disclaimer in
 **     the documentation and/or other materials provided with the
 **     distribution.
 **   * Neither the name of Nokia Corporation and its Subsidiary(-ies) nor
 **     the names of its contributors may be used to endorse or promote
 **     products derived from this software without specific prior written
 **     permission.
 **
 ** THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 ** "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 ** LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 ** A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 ** OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 ** SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 ** LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 ** DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 ** THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 ** (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 ** OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
 ** $QT_END_LICENSE$
 **
 ****************************************************************************/

 #include <QtGui>

 #include "robot.h"

 RobotPart::RobotPart(QGraphicsItem *parent)
     : QGraphicsObject(parent), color(Qt::lightGray), dragOver(false)
 {
     setAcceptDrops(true);
 }

 void RobotPart::dragEnterEvent(QGraphicsSceneDragDropEvent *event)
 {
     if (event->mimeData()->hasColor()) {
         event->setAccepted(true);
         dragOver = true;
         update();
     } else {
         event->setAccepted(false);
     }
 }

 void RobotPart::dragLeaveEvent(QGraphicsSceneDragDropEvent *event)
 {
     Q_UNUSED(event);
     dragOver = false;
     update();
 }

 void RobotPart::dropEvent(QGraphicsSceneDragDropEvent *event)
 {
     dragOver = false;
     if (event->mimeData()->hasColor())
         color = qVariantValue<QColor>(event->mimeData()->colorData());
     update();
 }

 RobotHead::RobotHead(QGraphicsItem *parent)
     : RobotPart(parent)
 {
 }

 QRectF RobotHead::boundingRect() const
 {
     return QRectF(-15, -50, 30, 50);
 }

 void RobotHead::paint(QPainter *painter,
            const QStyleOptionGraphicsItem *option, QWidget *widget)
 {
     Q_UNUSED(option);
     Q_UNUSED(widget);
     if (pixmap.isNull()) {
         painter->setBrush(dragOver ? color.light(130) : color);
         painter->drawRoundedRect(-10, -30, 20, 30, 25, 25, Qt::RelativeSize);
         painter->setBrush(Qt::white);
         painter->drawEllipse(-7, -3 - 20, 7, 7);
         painter->drawEllipse(0, -3 - 20, 7, 7);
         painter->setBrush(Qt::black);
         painter->drawEllipse(-5, -1 - 20, 2, 2);
         painter->drawEllipse(2, -1 - 20, 2, 2);
         painter->setPen(QPen(Qt::black, 2));
         painter->setBrush(Qt::NoBrush);
         painter->drawArc(-6, -2 - 20, 12, 15, 190 * 16, 160 * 16);
     } else {
         painter->scale(.2272, .2824);
         painter->drawPixmap(QPointF(-15 * 4.4, -50 * 3.54), pixmap);
     }
 }

 void RobotHead::dragEnterEvent(QGraphicsSceneDragDropEvent *event)
 {
     if (event->mimeData()->hasImage()) {
         event->setAccepted(true);
         dragOver = true;
         update();
     } else {
         RobotPart::dragEnterEvent(event);
     }
 }

 void RobotHead::dropEvent(QGraphicsSceneDragDropEvent *event)
 {
     if (event->mimeData()->hasImage()) {
         dragOver = false;
         pixmap = qVariantValue<QPixmap>(event->mimeData()->imageData());
         update();
     } else {
         RobotPart::dropEvent(event);
     }
 }

 RobotTorso::RobotTorso(QGraphicsItem *parent)
     : RobotPart(parent)
 {
 }

 QRectF RobotTorso::boundingRect() const
 {
     return QRectF(-30, -20, 60, 60);
 }

 void RobotTorso::paint(QPainter *painter,
            const QStyleOptionGraphicsItem *option, QWidget *widget)
 {
     Q_UNUSED(option);
     Q_UNUSED(widget);

     painter->setBrush(dragOver ? color.light(130) : color);
     painter->drawRoundedRect(-20, -20, 40, 60, 25, 25, Qt::RelativeSize);
     painter->drawEllipse(-25, -20, 20, 20);
     painter->drawEllipse(5, -20, 20, 20);
     painter->drawEllipse(-20, 22, 20, 20);
     painter->drawEllipse(0, 22, 20, 20);
 }

 RobotLimb::RobotLimb(QGraphicsItem *parent)
     : RobotPart(parent)
 {
 }

 QRectF RobotLimb::boundingRect() const
 {
     return QRectF(-5, -5, 40, 10);
 }

 void RobotLimb::paint(QPainter *painter,
            const QStyleOptionGraphicsItem *option, QWidget *widget)
 {
     Q_UNUSED(option);
     Q_UNUSED(widget);

     painter->setBrush(dragOver ? color.light(130) : color);
     painter->drawRoundedRect(boundingRect(), 50, 50, Qt::RelativeSize);
     painter->drawEllipse(-5, -5, 10, 10);
 }

 Robot::Robot(QGraphicsItem *parent)
     : RobotPart(parent)
 {
     setFlag(ItemHasNoContents);

     QGraphicsObject *torsoItem = new RobotTorso(this);
     QGraphicsObject *headItem = new RobotHead(torsoItem);
     QGraphicsObject *upperLeftArmItem = new RobotLimb(torsoItem);
     QGraphicsObject *lowerLeftArmItem = new RobotLimb(upperLeftArmItem);
     QGraphicsObject *upperRightArmItem = new RobotLimb(torsoItem);
     QGraphicsObject *lowerRightArmItem = new RobotLimb(upperRightArmItem);
     QGraphicsObject *upperRightLegItem = new RobotLimb(torsoItem);
     QGraphicsObject *lowerRightLegItem = new RobotLimb(upperRightLegItem);
     QGraphicsObject *upperLeftLegItem = new RobotLimb(torsoItem);
     QGraphicsObject *lowerLeftLegItem = new RobotLimb(upperLeftLegItem);

     headItem->setPos(0, -18);
     upperLeftArmItem->setPos(-15, -10);
     lowerLeftArmItem->setPos(30, 0);
     upperRightArmItem->setPos(15, -10);
     lowerRightArmItem->setPos(30, 0);
     upperRightLegItem->setPos(10, 32);
     lowerRightLegItem->setPos(30, 0);
     upperLeftLegItem->setPos(-10, 32);
     lowerLeftLegItem->setPos(30, 0);

     QParallelAnimationGroup *animation = new QParallelAnimationGroup(this);

     QPropertyAnimation *headAnimation = new QPropertyAnimation(headItem, "rotation");
     headAnimation->setStartValue(20);
     headAnimation->setEndValue(-20);
     QPropertyAnimation *headScaleAnimation = new QPropertyAnimation(headItem, "scale");
     headScaleAnimation->setEndValue(1.1);
     animation->addAnimation(headAnimation);
     animation->addAnimation(headScaleAnimation);

     QPropertyAnimation *upperLeftArmAnimation = new QPropertyAnimation(upperLeftArmItem, "rotation");
     upperLeftArmAnimation->setStartValue(190);
     upperLeftArmAnimation->setEndValue(180);
     animation->addAnimation(upperLeftArmAnimation);

     QPropertyAnimation *lowerLeftArmAnimation = new QPropertyAnimation(lowerLeftArmItem, "rotation");
     lowerLeftArmAnimation->setStartValue(50);
     lowerLeftArmAnimation->setEndValue(10);
     animation->addAnimation(lowerLeftArmAnimation);

     QPropertyAnimation *upperRightArmAnimation = new QPropertyAnimation(upperRightArmItem, "rotation");
     upperRightArmAnimation->setStartValue(300);
     upperRightArmAnimation->setEndValue(310);
     animation->addAnimation(upperRightArmAnimation);

     QPropertyAnimation *lowerRightArmAnimation = new QPropertyAnimation(lowerRightArmItem, "rotation");
     lowerRightArmAnimation->setStartValue(0);
     lowerRightArmAnimation->setEndValue(-70);
     animation->addAnimation(lowerRightArmAnimation);

     QPropertyAnimation *upperLeftLegAnimation = new QPropertyAnimation(upperLeftLegItem, "rotation");
     upperLeftLegAnimation->setStartValue(150);
     upperLeftLegAnimation->setEndValue(80);
     animation->addAnimation(upperLeftLegAnimation);

     QPropertyAnimation *lowerLeftLegAnimation = new QPropertyAnimation(lowerLeftLegItem, "rotation");
     lowerLeftLegAnimation->setStartValue(70);
     lowerLeftLegAnimation->setEndValue(10);
     animation->addAnimation(lowerLeftLegAnimation);

     QPropertyAnimation *upperRightLegAnimation = new QPropertyAnimation(upperRightLegItem, "rotation");
     upperRightLegAnimation->setStartValue(40);
     upperRightLegAnimation->setEndValue(120);
     animation->addAnimation(upperRightLegAnimation);

     QPropertyAnimation *lowerRightLegAnimation = new QPropertyAnimation(lowerRightLegItem, "rotation");
     lowerRightLegAnimation->setStartValue(10);
     lowerRightLegAnimation->setEndValue(50);
     animation->addAnimation(lowerRightLegAnimation);

     QPropertyAnimation *torsoAnimation = new QPropertyAnimation(torsoItem, "rotation");
     torsoAnimation->setStartValue(5);
     torsoAnimation->setEndValue(-20);
     animation->addAnimation(torsoAnimation);

     for (int i = 0; i < animation->animationCount(); ++i) {
         QPropertyAnimation *anim = qobject_cast<QPropertyAnimation *>(animation->animationAt(i));
         anim->setEasingCurve(QEasingCurve::SineCurve);
         anim->setDuration(2000);
     }

     animation->setLoopCount(-1);
     animation->start();
 }

 QRectF Robot::boundingRect() const
 {
     return QRectF();
 }

 void Robot::paint(QPainter *painter,
                   const QStyleOptionGraphicsItem *option, QWidget *widget)
 {
     Q_UNUSED(painter);
     Q_UNUSED(option);
     Q_UNUSED(widget);
 }
